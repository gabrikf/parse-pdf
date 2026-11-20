"""A storage failure on one file cancels the others before the error reaches the controller."""

import asyncio
from typing import cast

import pytest

from app.documents.domain.parser_kind import ParserKind
from app.documents.services.pdf_inspector import PdfInspector
from app.documents.use_cases.upload_documents import UploadCommand, UploadDocumentsUseCase
from app.parsers.pdf_tools import Inspection, InspectionVerdict
from app.repositories.document_repository import DocumentRepository
from app.storage.object_storage import ObjectStorage
from tests.fakes import FakeBudget, FakeClock
from tests.pdf_factory import make_text_pdf

ONE_PAGE = make_text_pdf(1)


class StorageDownError(Exception):
    """The bucket refused a write."""


class MemoryFile:
    """One uploaded file held in memory."""

    def __init__(self, name: str) -> None:
        self._name = name

    @property
    def filename(self) -> str | None:
        return self._name

    @property
    def size(self) -> int:
        return len(ONE_PAGE)

    async def read_head(self, count: int) -> bytes:
        return ONE_PAGE[:count]

    async def read_all(self) -> bytes:
        return ONE_PAGE


class OkInspector:
    async def inspect(self, data: bytes, password: str | None) -> Inspection:
        del data, password
        return Inspection(InspectionVerdict.OK, page_count=1)


class FirstPutFails:
    """The first write fails at once; every other write waits until it is cancelled."""

    def __init__(self) -> None:
        self.calls = 0
        self.cancelled = 0

    async def put(self, key: str, data: bytes) -> None:
        del key, data
        self.calls += 1
        if self.calls == 1:
            await asyncio.sleep(0.05)
            raise StorageDownError
        try:
            await asyncio.Event().wait()
        except asyncio.CancelledError:
            self.cancelled += 1
            raise


async def test_one_failed_write_cancels_the_other_files_and_keeps_its_error() -> None:
    storage = FirstPutFails()
    budget = FakeBudget()
    use_case = UploadDocumentsUseCase(
        cast("DocumentRepository", object()),
        cast("ObjectStorage", storage),
        cast("PdfInspector", OkInspector()),
        budget,
        FakeClock(),
    )
    files = [MemoryFile(f"{n}.pdf") for n in range(3)]
    command = UploadCommand("session", ParserKind.GEMINI, list(files))

    with pytest.raises(StorageDownError):
        await use_case.execute(command)

    assert storage.cancelled == 2
    assert budget.used == 0
