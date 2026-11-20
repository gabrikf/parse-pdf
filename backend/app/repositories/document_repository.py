"""Port: where document records, pages, chunks and the feed index live (door 1)."""

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from typing import Protocol

from app.documents.domain.document import Document
from app.documents.domain.document_status import DocumentStatus, FeedState
from app.documents.domain.page import Page
from app.documents.domain.parser_kind import ParserKind


class RunStartOutcome(StrEnum):
    """What the worker found when it tried to start a run."""

    STARTED = "started"
    STALE = "stale"
    ALREADY_FINAL = "already_final"
    EXHAUSTED = "exhausted"


@dataclass(frozen=True, slots=True)
class RunStart:
    """Result of ``begin_run``: the outcome and, when it exists, the document."""

    outcome: RunStartOutcome
    document: Document | None


@dataclass(frozen=True, slots=True)
class FeedPage:
    """One page of a session's feed, newest first."""

    items: list[Document]
    next_cursor: str | None


@dataclass(frozen=True, slots=True)
class FinalResult:
    """What a finished run saves in one atomic step."""

    status: DocumentStatus
    pages: list[Page]
    summary: str | None = None
    error_code: str | None = None
    hint: str | None = None


class InvalidCursorError(ValueError):
    """The feed cursor was not issued by this repository."""


class DocumentRepository(Protocol):
    """Atomic document storage. Every status change is a compare-and-set on ``run_id``."""

    async def create(self, document: Document, enqueue: bool) -> None:
        """Save a new record, index it in its session's feed, and queue it when asked."""
        ...

    async def get(self, document_id: str) -> Document | None:
        """Return the record, or None when it does not exist (or expired)."""
        ...

    async def list_feed(
        self, session_id: str, state: FeedState, cursor: str | None, limit: int
    ) -> FeedPage:
        """Return the session's documents in ``state``, newest first."""
        ...

    async def count_feed(self, session_id: str) -> dict[FeedState, int]:
        """Return how many documents the session holds in each feed group."""
        ...

    async def pages(self, document_id: str, offset: int, limit: int) -> tuple[list[Page], int]:
        """Return a slice of pages and the total page count."""
        ...

    async def restart_run(
        self,
        document: Document,
        allowed_from: frozenset[DocumentStatus],
        parser: ParserKind,
        run_id: str,
        at: datetime,
    ) -> Document | None:
        """Queue a final document again with a new run, clearing its results.

        Returns None when the status changed since ``document`` was read (a concurrent
        reparse won the compare-and-set).
        """
        ...

    async def delete(self, document: Document) -> bool:
        """Remove the record, pages, chunks and feed entries unless it is processing."""
        ...

    async def begin_run(
        self, document_id: str, run_id: str, max_deliveries: int, at: datetime
    ) -> RunStart:
        """Count a delivery and mark ``processing`` when the run is current."""
        ...

    async def note_failure(self, document_id: str, run_id: str, cause: str) -> None:
        """Record why a delivery of the current run failed (shown when the tries run out)."""
        ...

    async def save_chunk(
        self, document_id: str, run_id: str, index: int, pages: list[Page]
    ) -> None:
        """Checkpoint the pages of one model chunk."""
        ...

    async def load_chunks(self, document_id: str) -> dict[int, list[Page]]:
        """Return the chunks checkpointed so far for the current run."""
        ...

    async def finalize(
        self, document_id: str, run_id: str, result: FinalResult, at: datetime
    ) -> bool:
        """Save pages, summary and the final status if ``run_id`` is still current."""
        ...
