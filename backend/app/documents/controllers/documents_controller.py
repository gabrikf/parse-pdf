"""Read and change one session's documents: feed, document, pages, reparse, requeue, delete."""

from fastapi import APIRouter
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from app.core.errors import AppError
from app.documents.controllers.responses import ok
from app.documents.controllers.schemas.document_dto import counts_dto, document_dto, page_dto
from app.documents.controllers.schemas.query_params import parse_bounded_int, parse_state
from app.documents.controllers.session_dependency import Services, Session
from app.documents.domain.parser_kind import ParserKind
from app.repositories.document_repository import InvalidCursorError

router = APIRouter(prefix="/api/v1/documents", tags=["documents"])


class ReparseBody(BaseModel):
    """``{"parser": "<one of the three>"}``."""

    parser: str | None = None


def require_parser(raw: str | None) -> ParserKind:
    """Return the parser for an exact value, or raise ``422 invalid_parser``."""
    kind = ParserKind.parse(raw)
    if kind is None:
        allowed = {"allowed": ParserKind.allowed()}
        raise AppError(422, "invalid_parser", "Unknown parser.", allowed)
    return kind


@router.get("")
async def list_documents(
    session: Session,
    services: Services,
    state: str | None = None,
    cursor: str | None = None,
    limit: str | None = None,
) -> JSONResponse:
    """The session's documents, newest first, 20 by default and at most 50."""
    size = parse_bounded_int(limit, 20, 1, 50, "invalid_limit")
    feed_state = parse_state(state)
    try:
        page, counts = await services.list_documents.execute(
            session.session_id, feed_state, cursor, size
        )
    except InvalidCursorError:
        raise AppError(422, "invalid_cursor", "The cursor is not valid.") from None

    meta = {"next_cursor": page.next_cursor, "limit": size, "counts": counts_dto(counts)}
    meta["total"] = counts[feed_state]
    return ok([document_dto(document) for document in page.items], meta=meta)


@router.get("/{document_id}")
async def get_document(document_id: str, session: Session, services: Services) -> JSONResponse:
    """One document of the session."""
    document = await services.get_document.execute(session.session_id, document_id)
    return ok(document_dto(document))


@router.get("/{document_id}/pages")
async def get_pages(
    document_id: str,
    session: Session,
    services: Services,
    offset: str | None = None,
    limit: str | None = None,
) -> JSONResponse:
    """Pages of a ready document, 50 by default and at most 100."""
    start = parse_bounded_int(offset, 0, 0, 1_000_000, "invalid_offset")
    size = parse_bounded_int(limit, 50, 1, 100, "invalid_limit")
    result = await services.get_pages.execute(session.session_id, document_id, start, size)
    meta = {"total": result.total, "offset": start, "limit": size}
    return ok([page_dto(page) for page in result.pages], meta=meta)


@router.post("/{document_id}/reparse")
async def reparse(
    document_id: str, body: ReparseBody, session: Session, services: Services
) -> JSONResponse:
    """Queue a final document again with any parser."""
    parser = require_parser(body.parser)
    document = await services.reparse.execute(session.session_id, document_id, parser)
    return ok(document_dto(document), status=202)


@router.post("/{document_id}/requeue")
async def requeue(document_id: str, session: Session, services: Services) -> JSONResponse:
    """Retry a dead document with its parser."""
    document = await services.requeue.execute(session.session_id, document_id)
    return ok(document_dto(document), status=202)


@router.delete("/{document_id}")
async def delete(document_id: str, session: Session, services: Services) -> JSONResponse:
    """Delete a document that is not processing."""
    deleted_id = await services.delete.execute(session.session_id, document_id)
    return ok({"id": deleted_id, "deleted": True})
