"""Accept an upload: judge each file on its own, store the good ones, queue them (D4)."""

import asyncio
from dataclasses import dataclass, field, replace
from datetime import datetime, timedelta
from typing import Protocol

from app.core.clock import Clock
from app.core.ids import new_id
from app.documents.domain.document import Document
from app.documents.domain.document_status import DocumentStatus
from app.documents.domain.parser_kind import ParserKind
from app.documents.domain.rejection import Rejection, RejectionCode
from app.documents.services.filename import clean_filename
from app.documents.services.pdf_inspector import PdfInspector
from app.documents.services.pdf_validation import MAGIC_WINDOW_BYTES, is_too_large, precheck
from app.parsers.pdf_tools import InspectionVerdict
from app.rate_limit.model_budget import ModelBudget
from app.repositories.document_repository import DocumentRepository
from app.storage.object_storage import ObjectStorage, object_key_for

FILES_IN_PARALLEL = 3
VERDICT_REJECTIONS = {
    InspectionVerdict.LOCKED: RejectionCode.LOCKED,
    InspectionVerdict.UNLOCK_FAILED: RejectionCode.UNLOCK_FAILED,
    InspectionVerdict.UNREADABLE: RejectionCode.UNREADABLE_PDF,
}


class IncomingFile(Protocol):
    """One file of the multipart body, independent of the web framework."""

    @property
    def filename(self) -> str | None:
        """The name the client sent."""
        ...

    @property
    def size(self) -> int:
        """The byte count the server counted."""
        ...

    async def read_head(self, count: int) -> bytes:
        """Return the first ``count`` bytes."""
        ...

    async def read_all(self) -> bytes:
        """Return the whole file."""
        ...


@dataclass(frozen=True, slots=True)
class UploadCommand:
    """Who uploads, with which parser, which files, and an optional password for all of them."""

    session_id: str
    parser: ParserKind
    files: list[IncomingFile]
    password: str | None = None


@dataclass
class UploadResult:
    """Stored documents (``queued`` or ``too_large``) and refused files, in upload order."""

    documents: list[Document] = field(default_factory=list)
    rejected: list[Rejection] = field(default_factory=list)


class UploadDocumentsUseCase:
    """For each file: precheck, size, inspection, budget, then store and queue atomically."""

    def __init__(
        self,
        repository: DocumentRepository,
        storage: ObjectStorage,
        inspector: PdfInspector,
        budget: ModelBudget,
        clock: Clock,
    ) -> None:
        self._repository = repository
        self._storage = storage
        self._inspector = inspector
        self._budget = budget
        self._clock = clock

    async def execute(self, command: UploadCommand) -> UploadResult:
        """Judge every file; one bad file never fails the others."""
        slots = asyncio.Semaphore(FILES_IN_PARALLEL)
        now = self._clock.now()

        async def judge(index: int, file: IncomingFile) -> Document | Rejection:
            async with slots:
                # One millisecond per position keeps the feed order equal to the upload order.
                return await self._accept(command, file, now + timedelta(milliseconds=index))

        outcomes = await asyncio.gather(*(judge(i, f) for i, f in enumerate(command.files)))

        result = UploadResult()
        for outcome in outcomes:
            if isinstance(outcome, Document):
                result.documents.append(outcome)
            else:
                result.rejected.append(outcome)
        return result

    async def _accept(
        self, command: UploadCommand, file: IncomingFile, created: datetime
    ) -> Document | Rejection:
        name = clean_filename(file.filename)
        refused = precheck(file.size, await file.read_head(MAGIC_WINDOW_BYTES))
        if refused is not None:
            return Rejection(name, refused)

        draft = self._draft(command, name, file.size, created)
        if is_too_large(file.size):
            return await self._save_too_large(draft, page_count=0)

        data = await file.read_all()
        inspection = await self._inspector.inspect(data, command.password)
        if inspection.verdict is InspectionVerdict.TOO_MANY_PAGES:
            return await self._save_too_large(draft, inspection.page_count)
        if inspection.verdict in VERDICT_REJECTIONS:
            return Rejection(name, VERDICT_REJECTIONS[inspection.verdict])

        pages = inspection.page_count
        if command.parser.uses_model and not await self._budget.reserve(pages):
            return Rejection(name, RejectionCode.MODEL_BUDGET_EXHAUSTED)

        key = object_key_for(draft.id)
        document = replace(draft, page_count=pages, object_key=key)
        try:
            # Only decrypted bytes are stored; the password itself is never kept (AD-014).
            await self._storage.put(key, inspection.decrypted or data)
            await self._repository.create(document, enqueue=True)
        except BaseException:
            if command.parser.uses_model:
                await self._budget.release(pages)
            raise
        return document

    def _draft(self, command: UploadCommand, name: str, size: int, created: datetime) -> Document:
        return Document(
            id=new_id(),
            session_id=command.session_id,
            filename=name,
            parser=command.parser,
            status=DocumentStatus.QUEUED,
            page_count=0,
            size_bytes=size,
            created_at=created,
            updated_at=created,
            run_id=new_id(),
        )

    async def _save_too_large(self, draft: Document, page_count: int) -> Document:
        document = replace(draft, status=DocumentStatus.TOO_LARGE, page_count=page_count)
        await self._repository.create(document, enqueue=False)
        return document
