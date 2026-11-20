"""Convert documents and pages to and from their Redis shapes."""

import json
from datetime import datetime

from app.core.clock import to_iso, to_millis
from app.documents.domain.document import Document
from app.documents.domain.document_status import DocumentStatus
from app.documents.domain.page import Page, PageFormat
from app.documents.domain.parser_kind import ParserKind


def document_to_fields(document: Document) -> dict[str, str]:
    """Flatten a document into hash fields; None values are left out."""
    fields = {
        "id": document.id,
        "session_id": document.session_id,
        "filename": document.filename,
        "parser": document.parser.value,
        "status": document.status.value,
        "page_count": str(document.page_count),
        "size_bytes": str(document.size_bytes),
        "created_at": to_iso(document.created_at),
        "created_ms": str(to_millis(document.created_at)),
        "updated_at": to_iso(document.updated_at),
        "run_id": document.run_id,
        "deliveries": str(document.deliveries),
        "object_key": document.object_key,
        "error_code": document.error_code,
        "hint": document.hint,
        "summary": document.summary,
    }
    return {key: value for key, value in fields.items() if value is not None}


def document_from_fields(fields: dict[str, str]) -> Document:
    """Rebuild a document from its hash fields."""
    return Document(
        id=fields["id"],
        session_id=fields["session_id"],
        filename=fields["filename"],
        parser=ParserKind(fields["parser"]),
        status=DocumentStatus(fields["status"]),
        page_count=int(fields["page_count"]),
        size_bytes=int(fields["size_bytes"]),
        created_at=datetime.fromisoformat(fields["created_at"]),
        updated_at=datetime.fromisoformat(fields["updated_at"]),
        run_id=fields["run_id"],
        object_key=fields.get("object_key"),
        error_code=fields.get("error_code"),
        hint=fields.get("hint"),
        summary=fields.get("summary"),
        deliveries=int(fields.get("deliveries", "0")),
    )


def page_to_json(page: Page) -> str:
    """Encode one page as ``{number, content, format}``."""
    return json.dumps({"number": page.number, "content": page.content, "format": page.format})


def page_from_json(raw: str) -> Page:
    """Decode one page."""
    data = json.loads(raw)
    return Page(number=data["number"], content=data["content"], format=PageFormat(data["format"]))


def pages_to_json(pages: list[Page]) -> str:
    """Encode a chunk of pages as one JSON array."""
    return json.dumps([json.loads(page_to_json(page)) for page in pages])


def pages_from_json(raw: str) -> list[Page]:
    """Decode a chunk of pages."""
    return [page_from_json(json.dumps(item)) for item in json.loads(raw)]
