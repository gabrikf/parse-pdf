"""Which user actions each status allows (state diagram in plan.md)."""

from app.documents.domain.document_status import DocumentStatus
from app.documents.domain.errors import (
    DocumentBusyError,
    NotDeadError,
    NotReparsableError,
)

BUSY = frozenset({DocumentStatus.QUEUED, DocumentStatus.PROCESSING})
REPARSABLE = frozenset({DocumentStatus.READY, DocumentStatus.NO_TEXT, DocumentStatus.DEAD})


def ensure_reparsable(status: DocumentStatus) -> None:
    """Allow reparse from ``ready``, ``no_text`` or ``dead``."""
    if status in BUSY:
        raise DocumentBusyError
    if status not in REPARSABLE:
        raise NotReparsableError


def ensure_requeueable(status: DocumentStatus) -> None:
    """Allow requeue (same parser) only from ``dead``."""
    if status in BUSY:
        raise DocumentBusyError
    if status is not DocumentStatus.DEAD:
        raise NotDeadError


def ensure_deletable(status: DocumentStatus) -> None:
    """Allow delete from every status but ``processing``."""
    if status is DocumentStatus.PROCESSING:
        raise DocumentBusyError
