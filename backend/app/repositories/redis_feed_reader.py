"""Read a session's feed pages from its sorted-set indexes."""

from typing import cast

from redis.asyncio import Redis

from app.documents.domain.document import Document
from app.documents.domain.document_status import FeedState
from app.repositories.document_codec import document_from_fields
from app.repositories.document_repository import FeedPage
from app.repositories.feed_cursor import FeedCursor
from app.repositories.redis_keys import doc_key, feed_key

SCAN_BATCH = 100


class RedisFeedReader:
    """Newest-first pagination with an opaque cursor; expired records are pruned on read."""

    def __init__(self, redis: Redis) -> None:
        self._redis = redis

    async def page(
        self, session_id: str, state: FeedState, cursor: FeedCursor | None, limit: int
    ) -> FeedPage:
        """Return up to ``limit`` documents after ``cursor``."""
        key = feed_key(session_id, state)
        members, more = await self._members_after(key, cursor, limit)
        documents = await self._load(session_id, [member for member, _ in members])

        next_cursor = None
        if more and members:
            last_member, last_score = members[-1]
            next_cursor = FeedCursor(score=last_score, member=last_member).encode()
        return FeedPage(items=documents, next_cursor=next_cursor)

    async def counts(self, session_id: str) -> dict[FeedState, int]:
        """Return the size of every feed group."""
        async with self._redis.pipeline(transaction=False) as pipe:
            for state in FeedState:
                pipe.zcard(feed_key(session_id, state))
            sizes = await pipe.execute()
        return dict(zip(FeedState, (int(size) for size in sizes), strict=True))

    async def _members_after(
        self, key: str, cursor: FeedCursor | None, limit: int
    ) -> tuple[list[tuple[str, int]], bool]:
        top = "+inf" if cursor is None else str(cursor.score)
        found: list[tuple[str, int]] = []
        offset = 0

        while True:
            rows = cast(
                "list[tuple[str, float]]",
                await self._redis.zrevrangebyscore(
                    key, top, "-inf", start=offset, num=SCAN_BATCH, withscores=True
                ),
            )
            for member, raw_score in rows:
                score = int(raw_score)
                if cursor is not None and not cursor.is_after(score, member):
                    continue
                found.append((member, score))
                if len(found) > limit:
                    return found[:limit], True
            if len(rows) < SCAN_BATCH:
                return found, False
            offset += SCAN_BATCH

    async def _load(self, session_id: str, ids: list[str]) -> list[Document]:
        async with self._redis.pipeline(transaction=False) as pipe:
            for document_id in ids:
                pipe.hgetall(doc_key(document_id))
            rows = cast("list[dict[str, str]]", await pipe.execute())

        documents: list[Document] = []
        expired: list[str] = []
        for document_id, fields in zip(ids, rows, strict=True):
            if fields:
                documents.append(document_from_fields(fields))
            else:
                expired.append(document_id)
        if expired:
            await self._prune(session_id, expired)
        return documents

    async def _prune(self, session_id: str, ids: list[str]) -> None:
        async with self._redis.pipeline(transaction=False) as pipe:
            for state in FeedState:
                pipe.zrem(feed_key(session_id, state), *ids)
            await pipe.execute()
