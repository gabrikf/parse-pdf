"""Response shapes of the documents API, built from domain values."""

from typing import Any

from app.core.clock import to_iso
from app.documents.domain.document import Document
from app.documents.domain.document_status import FeedState
from app.documents.domain.page import Page
from app.documents.domain.rejection import Rejection


def document_dto(document: Document) -> dict[str, Any]:
    """The public ``Document``; ``summary`` is set only when ``ready`` (AD-004)."""
    return {
        "id": document.id,
        "filename": document.filename,
        "parser": document.parser.value,
        "status": document.status.value,
        "error_code": document.error_code,
        "hint": document.hint,
        "page_count": document.page_count,
        "size_bytes": document.size_bytes,
        "created_at": to_iso(document.created_at),
        "updated_at": to_iso(document.updated_at),
        "summary": document.visible_summary,
    }


def rejection_dto(rejection: Rejection) -> dict[str, str]:
    """A refused file: ``{filename, code, message}``."""
    return {
        "filename": rejection.filename,
        "code": rejection.code.value,
        "message": rejection.message,
    }


def page_dto(page: Page) -> dict[str, Any]:
    """``{number, content, format}``."""
    return {"number": page.number, "content": page.content, "format": page.format.value}


def counts_dto(counts: dict[FeedState, int]) -> dict[str, int]:
    """Feed group sizes keyed by the ``state`` values."""
    return {state.value: count for state, count in counts.items()}
