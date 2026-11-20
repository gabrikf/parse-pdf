"""Pure pypdf functions. They run inside ``IsolatedRunner`` children, never in the event loop."""

import io
from dataclasses import dataclass
from enum import StrEnum

from pypdf import PasswordType, PdfReader, PdfWriter


class InspectionVerdict(StrEnum):
    """What opening the file showed."""

    OK = "ok"
    LOCKED = "password_required"
    UNLOCK_FAILED = "wrong_password"
    UNREADABLE = "unreadable_pdf"
    TOO_MANY_PAGES = "too_many_pages"


@dataclass(frozen=True, slots=True)
class Inspection:
    """The verdict, the page count, and decrypted bytes when the file was encrypted."""

    verdict: InspectionVerdict
    page_count: int = 0
    decrypted: bytes | None = None


def _unlock(reader: PdfReader, password: str | None) -> InspectionVerdict:
    if reader.decrypt("") != PasswordType.NOT_DECRYPTED:
        return InspectionVerdict.OK
    if not password:
        return InspectionVerdict.LOCKED
    if reader.decrypt(password) == PasswordType.NOT_DECRYPTED:
        return InspectionVerdict.UNLOCK_FAILED
    return InspectionVerdict.OK


def _write(reader: PdfReader) -> bytes:
    writer = PdfWriter(clone_from=reader)
    buffer = io.BytesIO()
    writer.write(buffer)
    return buffer.getvalue()


def inspect_pdf(data: bytes, password: str | None, max_pages: int) -> Inspection:
    """Open the PDF, unlock it if needed, and count its pages.

    An encrypted file that opens is rewritten without encryption, so workers and models only
    ever see plain PDFs and the password is never needed again.
    """
    try:
        reader = PdfReader(io.BytesIO(data), strict=False)
        encrypted = reader.is_encrypted
        if encrypted:
            verdict = _unlock(reader, password)
            if verdict is not InspectionVerdict.OK:
                return Inspection(verdict)

        page_count = len(reader.pages)
        if page_count > max_pages:
            return Inspection(InspectionVerdict.TOO_MANY_PAGES, page_count)

        decrypted = _write(reader) if encrypted else None
    except Exception:  # noqa: BLE001 - any pypdf failure means the file is unreadable
        return Inspection(InspectionVerdict.UNREADABLE)

    return Inspection(InspectionVerdict.OK, page_count, decrypted)


def extract_text_pages(data: bytes) -> list[str]:
    """Return the text of every page, in order (pypdf's plain-text extraction)."""
    reader = PdfReader(io.BytesIO(data), strict=False)
    return [page.extract_text() or "" for page in reader.pages]


def split_pdf(data: bytes, pages_per_chunk: int) -> list[tuple[bytes, int]]:
    """Split the PDF into ``(bytes, page_count)`` chunks; the last may be shorter."""
    reader = PdfReader(io.BytesIO(data), strict=False)
    total = len(reader.pages)
    chunks: list[tuple[bytes, int]] = []
    for start in range(0, total, pages_per_chunk):
        end = min(start + pages_per_chunk, total)
        writer = PdfWriter()
        for index in range(start, end):
            writer.add_page(reader.pages[index])
        buffer = io.BytesIO()
        writer.write(buffer)
        chunks.append((buffer.getvalue(), end - start))
    return chunks
