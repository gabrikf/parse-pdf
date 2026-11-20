"""The document record: what was uploaded, how it is parsed, and where it stands."""

from dataclasses import dataclass, replace
from datetime import datetime

from app.documents.domain.document_status import FINAL_STATUSES, DocumentStatus
from app.documents.domain.parser_kind import ParserKind


@dataclass(frozen=True, slots=True)
class Document:
    """One uploaded file. Immutable: every change produces a new value.

    ``run_id`` names the current queue run; a stream entry whose run differs is stale.
    ``summary`` is only exposed while the status is ``ready`` (AD-004).
    """

    id: str
    session_id: str
    filename: str
    parser: ParserKind
    status: DocumentStatus
    page_count: int
    size_bytes: int
    created_at: datetime
    updated_at: datetime
    run_id: str
    object_key: str | None = None
    error_code: str | None = None
    hint: str | None = None
    summary: str | None = None
    deliveries: int = 0

    @property
    def is_final(self) -> bool:
        """True for ``ready``, ``no_text`` and ``dead``."""
        return self.status in FINAL_STATUSES

    @property
    def visible_summary(self) -> str | None:
        """The summary, or None unless the document is ready."""
        return self.summary if self.status is DocumentStatus.READY else None

    def with_status(self, status: DocumentStatus, at: datetime) -> "Document":
        """Return a copy in ``status``, stamped ``at``."""
        return replace(self, status=status, updated_at=at)
