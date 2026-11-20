"""Document statuses and the feed groups the page filters on (AD-022)."""

from enum import StrEnum


class DocumentStatus(StrEnum):
    """Where a document is in its life; see the state diagram in plan.md."""

    QUEUED = "queued"
    PROCESSING = "processing"
    READY = "ready"
    NO_TEXT = "no_text"
    TOO_LARGE = "too_large"
    DEAD = "dead"


class FeedState(StrEnum):
    """The ``state`` filter of ``GET /api/v1/documents``."""

    PARSED = "parsed"
    FAILED = "failed"
    ACTIVE = "active"
    ALL = "all"


FINAL_STATUSES = frozenset({DocumentStatus.READY, DocumentStatus.NO_TEXT, DocumentStatus.DEAD})

STATUS_GROUP: dict[DocumentStatus, FeedState] = {
    DocumentStatus.QUEUED: FeedState.ACTIVE,
    DocumentStatus.PROCESSING: FeedState.ACTIVE,
    DocumentStatus.READY: FeedState.PARSED,
    DocumentStatus.NO_TEXT: FeedState.PARSED,
    DocumentStatus.DEAD: FeedState.FAILED,
    DocumentStatus.TOO_LARGE: FeedState.FAILED,
}


def group_of(status: DocumentStatus) -> FeedState:
    """Return the feed group a status belongs to (never ``all``)."""
    return STATUS_GROUP[status]
