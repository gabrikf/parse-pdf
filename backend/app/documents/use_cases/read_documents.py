"""Read use cases: one document, the feed, a document's pages, today's budget."""

from dataclasses import dataclass

from app.documents.domain.document import Document
from app.documents.domain.document_status import DocumentStatus, FeedState
from app.documents.domain.errors import NotReadyError
from app.documents.domain.page import Page
from app.documents.use_cases.ownership import load_owned
from app.rate_limit.model_budget import BudgetUsage, ModelBudget
from app.repositories.document_repository import DocumentRepository, FeedPage


@dataclass(frozen=True, slots=True)
class PagesSlice:
    """Pages ``offset`` onward and the document's page total."""

    pages: list[Page]
    total: int


class GetDocumentUseCase:
    """Return one of the session's documents."""

    def __init__(self, repository: DocumentRepository) -> None:
        self._repository = repository

    async def execute(self, session_id: str, document_id: str) -> Document:
        """Raise ``DocumentNotFoundError`` for an unknown or foreign id."""
        return await load_owned(self._repository, document_id, session_id)


class ListDocumentsUseCase:
    """Return a page of the session's feed, newest first, with every group's count."""

    def __init__(self, repository: DocumentRepository) -> None:
        self._repository = repository

    async def execute(
        self, session_id: str, state: FeedState, cursor: str | None, limit: int
    ) -> tuple[FeedPage, dict[FeedState, int]]:
        """Return the page and the counts the chips show."""
        page = await self._repository.list_feed(session_id, state, cursor, limit)
        counts = await self._repository.count_feed(session_id)
        return page, counts


class GetPagesUseCase:
    """Return a ready document's pages; any other status is ``not_ready`` (AD-004)."""

    def __init__(self, repository: DocumentRepository) -> None:
        self._repository = repository

    async def execute(
        self, session_id: str, document_id: str, offset: int, limit: int
    ) -> PagesSlice:
        """Return ``limit`` pages from ``offset``."""
        document = await load_owned(self._repository, document_id, session_id)
        if document.status is not DocumentStatus.READY:
            raise NotReadyError
        pages, total = await self._repository.pages(document_id, offset, limit)
        return PagesSlice(pages=pages, total=total)


class GetBudgetUseCase:
    """Return today's model page usage."""

    def __init__(self, budget: ModelBudget) -> None:
        self._budget = budget

    async def execute(self) -> BudgetUsage:
        """Read the counter."""
        return await self._budget.usage()
