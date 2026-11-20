"""Write documents straight into Redis, in any status, for read-side tests."""

from datetime import UTC, datetime, timedelta

from redis.asyncio import Redis

from app.core.ids import new_id
from app.documents.domain.document import Document
from app.documents.domain.document_status import DocumentStatus
from app.documents.domain.page import Page, PageFormat
from app.documents.domain.parser_kind import ParserKind
from app.repositories.document_repository import FinalResult
from app.repositories.redis_document_repository import RedisDocumentRepository

BASE_TIME = datetime(2026, 11, 19, 12, 0, tzinfo=UTC)


def draft(
    session_id: str,
    index: int = 0,
    status: DocumentStatus = DocumentStatus.QUEUED,
    parser: ParserKind = ParserKind.PYPDF,
    page_count: int = 1,
) -> Document:
    """A document created ``index`` seconds after the base time."""
    at = BASE_TIME + timedelta(seconds=index)
    document_id = new_id()
    return Document(
        id=document_id,
        session_id=session_id,
        filename=f"doc-{index}.pdf",
        parser=parser,
        status=status,
        page_count=page_count,
        size_bytes=1000,
        created_at=at,
        updated_at=at,
        run_id=new_id(),
        object_key=f"documents/{document_id}.pdf",
    )


async def seed(
    redis: Redis,
    session_id: str,
    index: int,
    status: DocumentStatus,
    *,
    pages: list[str] | None = None,
    summary: str = "A summary.",
) -> Document:
    """Create a document and drive it to ``status`` through the real scripts."""
    repository = RedisDocumentRepository(redis)
    document = draft(session_id, index)
    if status is DocumentStatus.TOO_LARGE:
        document = draft(session_id, index, status=DocumentStatus.TOO_LARGE)
        await repository.create(document, enqueue=False)
        return document

    await repository.create(document, enqueue=True)
    if status is DocumentStatus.QUEUED:
        return document

    await repository.begin_run(document.id, document.run_id, 5, BASE_TIME)
    if status is DocumentStatus.PROCESSING:
        return document

    texts = pages if pages is not None else ["page one"]
    page_list = [Page(n, text, PageFormat.TEXT) for n, text in enumerate(texts, 1)]
    result = {
        DocumentStatus.READY: FinalResult(DocumentStatus.READY, page_list, summary=summary),
        DocumentStatus.NO_TEXT: FinalResult(DocumentStatus.NO_TEXT, page_list, hint="try gemini"),
        DocumentStatus.DEAD: FinalResult(DocumentStatus.DEAD, [], error_code="provider_rejected"),
    }[status]
    await repository.finalize(document.id, document.run_id, result, BASE_TIME)
    return document
