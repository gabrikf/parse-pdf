"""Cheap checks made before a file is opened: emptiness, PDF signature, size."""

from app.documents.domain.rejection import RejectionCode

PDF_MAGIC = b"%PDF-"
MAGIC_WINDOW_BYTES = 1024
MAX_FILE_BYTES = 52_428_800
MAX_PAGES = 1000


def precheck(size: int, head: bytes) -> RejectionCode | None:
    """Return why a file is refused before parsing, or None.

    The signature is searched in the first 1,024 bytes, as PDF readers do, so the file's name
    or declared type never decides: a PNG named ``scan.pdf`` is refused, a PDF named
    ``report.txt`` is accepted.
    """
    if size == 0:
        return RejectionCode.EMPTY
    if PDF_MAGIC not in head[:MAGIC_WINDOW_BYTES]:
        return RejectionCode.NOT_PDF
    return None


def is_too_large(size: int) -> bool:
    """True above 50 MiB (52,428,800 bytes)."""
    return size > MAX_FILE_BYTES
