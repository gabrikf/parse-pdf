"""The worker's use case: run one queue entry from claim to final status (AD-002, AD-005)."""

from enum import StrEnum

from app.core.clock import Clock
from app.core.logging import get_logger
from app.documents.domain.document import Document
from app.documents.domain.document_status import DocumentStatus
from app.documents.domain.failure_cause import UNEXPECTED_CAUSE, describe_cause
from app.documents.domain.job_errors import PermanentFailure, TransientFailure
from app.documents.domain.page import Page
from app.documents.domain.parser_kind import ParserKind
from app.documents.services.parser_selector import ParserSelector
from app.documents.services.summary_service import SummaryService
from app.parsers.page_parser import ParseRequest
from app.queue.job import DeadLetter, Job
from app.queue.job_queue import JobQueue
from app.repositories.document_repository import (
    DocumentRepository,
    FinalResult,
    RunStartOutcome,
)
from app.storage.object_storage import ObjectStorage

NO_TEXT_HINT = (
    "This usually means a scanned PDF or a photo of a page. "
    f"Try the {ParserKind.GEMINI.value} parser, which reads scans."
)
log = get_logger("process_document")


class JobOutcome(StrEnum):
    """Whether the entry was acknowledged or left pending for redelivery."""

    ACKED = "acked"
    PENDING = "pending"


class RepositoryCheckpoint:
    """``ChunkCheckpoint`` bound to one run of one document."""

    def __init__(self, repository: DocumentRepository, document_id: str, run_id: str) -> None:
        self._repository = repository
        self._document_id = document_id
        self._run_id = run_id

    async def load(self) -> dict[int, list[Page]]:
        """Return the chunks saved for this run."""
        return await self._repository.load_chunks(self._document_id)

    async def save(self, index: int, pages: list[Page]) -> None:
        """Save one chunk for this run."""
        await self._repository.save_chunk(self._document_id, self._run_id, index, pages)


class ProcessDocumentUseCase:
    """Claim, parse, summarize, save, then acknowledge - in that order.

    A stale entry (old ``run_id`` or deleted document) and an entry whose run is already final
    are acknowledged with no parser or model call. The 6th delivery ends ``dead``. A transient
    failure leaves the entry pending, so another delivery retries it.
    """

    def __init__(
        self,
        repository: DocumentRepository,
        queue: JobQueue,
        storage: ObjectStorage,
        parsers: ParserSelector,
        summaries: SummaryService,
        *,
        clock: Clock,
        max_deliveries: int,
    ) -> None:
        self._repository = repository
        self._queue = queue
        self._storage = storage
        self._parsers = parsers
        self._summaries = summaries
        self._clock = clock
        self._max_deliveries = max_deliveries

    async def execute(self, job: Job) -> JobOutcome:
        """Process one entry and say what happened to it."""
        start = await self._repository.begin_run(
            job.document_id, job.run_id, self._max_deliveries, self._clock.now()
        )
        bound = log.bind(document_id=job.document_id, run_id=job.run_id)

        if start.outcome is RunStartOutcome.EXHAUSTED and start.document is not None:
            await self._dead_letter(start.document, "max_deliveries")
        if start.outcome is not RunStartOutcome.STARTED or start.document is None:
            bound.info("job_skipped", outcome=start.outcome.value)
            await self._queue.ack(job)
            return JobOutcome.ACKED

        try:
            result = await self._run(start.document)
        except PermanentFailure as failure:
            bound.warning("job_failed", error_code=failure.code)
            result = FinalResult(
                DocumentStatus.DEAD, pages=[], error_code=failure.code, hint=failure.hint
            )
            await self._dead_letter(start.document, failure.code)
        except TransientFailure as failure:
            bound.warning("job_left_pending", deliveries=start.document.deliveries)
            await self._note(job, describe_cause(str(failure)))
            return JobOutcome.PENDING
        except Exception:
            await self._note(job, UNEXPECTED_CAUSE)
            raise

        await self._repository.finalize(job.document_id, job.run_id, result, self._clock.now())
        await self._queue.ack(job)
        bound.info("job_done", status=result.status.value)
        return JobOutcome.ACKED

    async def _run(self, document: Document) -> FinalResult:
        pdf = await self._storage.get(document.object_key or "")
        checkpoint = RepositoryCheckpoint(self._repository, document.id, document.run_id)
        parser = self._parsers.pick(document.parser)
        pages = await parser.parse(ParseRequest(document, pdf, checkpoint))

        if all(page.is_blank for page in pages):
            return FinalResult(DocumentStatus.NO_TEXT, pages=pages, hint=NO_TEXT_HINT)

        summary = await self._summaries.summarize(pages)
        return FinalResult(DocumentStatus.READY, pages=pages, summary=summary)

    async def _note(self, job: Job, cause: str) -> None:
        """Keep the cause for the ``max_deliveries`` hint; never mask the failure being handled."""
        try:
            await self._repository.note_failure(job.document_id, job.run_id, cause)
        except Exception:
            log.exception("note_failure_failed", document_id=job.document_id)

    async def _dead_letter(self, document: Document, error_code: str) -> None:
        letter = DeadLetter(document.id, document.run_id, error_code, document.deliveries)
        await self._queue.dead_letter(letter)
