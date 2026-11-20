"""Reparse (any parser) and requeue (same parser) a final document."""

from app.core.clock import Clock
from app.core.ids import new_id
from app.documents.domain.document import Document
from app.documents.domain.document_status import DocumentStatus
from app.documents.domain.errors import DocumentBusyError, ModelBudgetExhaustedError
from app.documents.domain.parser_kind import ParserKind
from app.documents.domain.transitions import REPARSABLE, ensure_reparsable, ensure_requeueable
from app.documents.use_cases.ownership import load_owned
from app.rate_limit.model_budget import ModelBudget
from app.repositories.document_repository import DocumentRepository


class BudgetedRestart:
    """Reserve the model pages a new run will send, then restart it; release them if it loses.

    Every rerun parses every page again (the chunk checkpoints are cleared), so a model parser
    counts the whole document against the daily budget each time.
    """

    def __init__(self, repository: DocumentRepository, budget: ModelBudget, clock: Clock) -> None:
        self._repository = repository
        self._budget = budget
        self._clock = clock

    async def __call__(
        self, document: Document, allowed: frozenset[DocumentStatus], parser: ParserKind
    ) -> Document:
        """Return the queued document, or raise when the budget or the status refuses it."""
        reserved = parser.uses_model
        if reserved and not await self._budget.reserve(document.page_count):
            raise ModelBudgetExhaustedError

        queued = await self._repository.restart_run(
            document, allowed, parser, new_id(), self._clock.now()
        )
        if queued is None:
            if reserved:
                await self._budget.release(document.page_count)
            raise DocumentBusyError
        return queued


class ReparseDocumentUseCase:
    """Queue a ``ready``, ``no_text`` or ``dead`` document again with any parser.

    The status check, the new ``run_id``, the cleared results and the stream entry are one
    compare-and-set, so of two concurrent reparses exactly one wins (the other is busy).
    """

    def __init__(self, repository: DocumentRepository, budget: ModelBudget, clock: Clock) -> None:
        self._repository = repository
        self._restart = BudgetedRestart(repository, budget, clock)

    async def execute(self, session_id: str, document_id: str, parser: ParserKind) -> Document:
        """Return the queued document."""
        document = await load_owned(self._repository, document_id, session_id)
        ensure_reparsable(document.status)

        return await self._restart(document, REPARSABLE, parser)


class RequeueDocumentUseCase:
    """Retry a ``dead`` document with the parser it already has, inside the daily budget."""

    def __init__(self, repository: DocumentRepository, budget: ModelBudget, clock: Clock) -> None:
        self._repository = repository
        self._restart = BudgetedRestart(repository, budget, clock)

    async def execute(self, session_id: str, document_id: str) -> Document:
        """Return the queued document."""
        document = await load_owned(self._repository, document_id, session_id)
        ensure_requeueable(document.status)

        return await self._restart(document, frozenset({DocumentStatus.DEAD}), document.parser)
