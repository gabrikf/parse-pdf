"""``DocumentRepository`` on Redis: hashes, lists, sorted sets and the Lua scripts of door 1."""

from datetime import datetime
from typing import cast

from redis.asyncio import Redis

from app.core.clock import to_iso
from app.documents.domain.document import Document
from app.documents.domain.document_status import DocumentStatus, FeedState, group_of
from app.documents.domain.page import Page
from app.documents.domain.parser_kind import ParserKind
from app.queue.job import STREAM_KEY
from app.repositories.document_codec import (
    document_from_fields,
    document_to_fields,
    page_from_json,
    page_to_json,
    pages_from_json,
    pages_to_json,
)
from app.repositories.document_repository import (
    FeedPage,
    FinalResult,
    InvalidCursorError,
    RunStart,
    RunStartOutcome,
)
from app.repositories.feed_cursor import FeedCursor
from app.repositories.lua_scripts import DocumentScripts
from app.repositories.redis_feed_reader import RedisFeedReader
from app.repositories.redis_keys import DOCUMENT_TTL_S, chunks_key, doc_key, feed_key, pages_key


class RedisDocumentRepository:
    """Every write is one Lua script, so no reader ever sees half a change."""

    def __init__(self, redis: Redis, ttl_s: int = DOCUMENT_TTL_S) -> None:
        self._redis = redis
        self._ttl = ttl_s
        self._scripts = DocumentScripts.register(redis)
        self._feed = RedisFeedReader(redis)

    async def create(self, document: Document, enqueue: bool) -> None:
        """Save, index and (for ``queued``) enqueue in one script."""
        fields = document_to_fields(document)
        flat = [item for pair in fields.items() for item in pair]
        keys = [
            doc_key(document.id),
            feed_key(document.session_id),
            feed_key(document.session_id, group_of(document.status)),
            STREAM_KEY,
        ]
        args: list[str | int] = [self._ttl, fields["created_ms"], document.id, int(enqueue)]
        args += [document.object_key or "", document.run_id, *flat]
        await self._scripts.create(keys=keys, args=args)

    async def get(self, document_id: str) -> Document | None:
        """Return the record or None."""
        fields = cast("dict[str, str]", await self._redis.hgetall(doc_key(document_id)))
        return document_from_fields(fields) if fields else None

    async def list_feed(
        self, session_id: str, state: FeedState, cursor: str | None, limit: int
    ) -> FeedPage:
        """Return one feed page; an unknown cursor raises ``InvalidCursorError``."""
        try:
            position = FeedCursor.decode(cursor) if cursor else None
        except ValueError as exc:
            raise InvalidCursorError(str(exc)) from exc
        return await self._feed.page(session_id, state, position, limit)

    async def count_feed(self, session_id: str) -> dict[FeedState, int]:
        """Return the size of every feed group."""
        return await self._feed.counts(session_id)

    async def pages(self, document_id: str, offset: int, limit: int) -> tuple[list[Page], int]:
        """Return pages ``offset`` to ``offset + limit - 1`` and the total."""
        async with self._redis.pipeline(transaction=False) as pipe:
            pipe.lrange(pages_key(document_id), offset, offset + limit - 1)
            pipe.llen(pages_key(document_id))
            rows, total = await pipe.execute()
        return [page_from_json(row) for row in rows], int(total)

    async def restart_run(
        self,
        document: Document,
        allowed_from: frozenset[DocumentStatus],
        parser: ParserKind,
        run_id: str,
        at: datetime,
    ) -> Document | None:
        """Requeue with a new run if the status is still one of ``allowed_from``."""
        sid = document.session_id
        keys = [
            doc_key(document.id),
            pages_key(document.id),
            chunks_key(document.id),
            feed_key(sid),
            feed_key(sid, FeedState.PARSED),
            feed_key(sid, FeedState.FAILED),
            feed_key(sid, FeedState.ACTIVE),
            STREAM_KEY,
        ]
        allowed = ",".join(sorted(status.value for status in allowed_from))
        args: list[str | int] = [allowed, run_id, parser.value, to_iso(at), self._ttl]
        args += [document.id, document.object_key or ""]
        if int(await self._scripts.restart_run(keys=keys, args=args)) != 1:
            return None
        return await self.get(document.id)

    async def delete(self, document: Document) -> bool:
        """Delete unless processing; False when the script refused."""
        sid = document.session_id
        keys = [doc_key(document.id), pages_key(document.id), chunks_key(document.id)]
        keys += [feed_key(sid, state) for state in FeedState]
        return int(await self._scripts.delete(keys=keys, args=[document.id])) == 1

    async def begin_run(
        self, document_id: str, run_id: str, max_deliveries: int, at: datetime
    ) -> RunStart:
        """Count the delivery and mark ``processing`` if the run is current."""
        document = await self.get(document_id)
        if document is None:
            return RunStart(RunStartOutcome.STALE, None)

        sid = document.session_id
        keys = [
            doc_key(document_id),
            feed_key(sid),
            feed_key(sid, FeedState.ACTIVE),
            feed_key(sid, FeedState.FAILED),
            pages_key(document_id),
            chunks_key(document_id),
        ]
        args: list[str | int] = [run_id, max_deliveries, to_iso(at), self._ttl, document_id]
        outcome, _ = await self._scripts.begin_run(keys=keys, args=args)
        return RunStart(RunStartOutcome(outcome), await self.get(document_id))

    async def save_chunk(
        self, document_id: str, run_id: str, index: int, pages: list[Page]
    ) -> None:
        """Checkpoint a chunk if the run is still current."""
        keys = [doc_key(document_id), chunks_key(document_id)]
        args: list[str | int] = [run_id, index, pages_to_json(pages), self._ttl]
        await self._scripts.save_chunk(keys=keys, args=args)

    async def load_chunks(self, document_id: str) -> dict[int, list[Page]]:
        """Return the checkpointed chunks by index."""
        rows = cast("dict[str, str]", await self._redis.hgetall(chunks_key(document_id)))
        return {int(index): pages_from_json(raw) for index, raw in rows.items()}

    async def finalize(
        self, document_id: str, run_id: str, result: FinalResult, at: datetime
    ) -> bool:
        """Save the run's outcome; False when the run is no longer current."""
        document = await self.get(document_id)
        if document is None:
            return False

        sid = document.session_id
        keys = [
            doc_key(document_id),
            pages_key(document_id),
            chunks_key(document_id),
            feed_key(sid),
            feed_key(sid, FeedState.ACTIVE),
            feed_key(sid, group_of(result.status)),
        ]
        args: list[str | int] = [run_id, result.status.value, to_iso(at), self._ttl, document_id]
        args += [result.summary or "", result.error_code or "", result.hint or ""]
        args += [page_to_json(page) for page in result.pages]
        return int(await self._scripts.finalize(keys=keys, args=args)) == 1
