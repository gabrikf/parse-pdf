"""pypdf functions run in-process here (the workers run them in child processes)."""

from app.parsers.pdf_tools import InspectionVerdict, extract_text_pages, inspect_pdf, split_pdf
from tests.pdf_factory import encrypt, make_pdf, make_text_pdf


def test_plain_pdf_counts_pages_and_keeps_bytes() -> None:
    inspection = inspect_pdf(make_text_pdf(3), None, 1000)

    assert inspection.verdict is InspectionVerdict.OK
    assert inspection.page_count == 3
    assert inspection.decrypted is None


def test_more_pages_than_allowed() -> None:
    inspection = inspect_pdf(make_text_pdf(4), None, 3)

    assert inspection.verdict is InspectionVerdict.TOO_MANY_PAGES
    assert inspection.page_count == 4


def test_empty_password_pdf_opens_and_is_decrypted() -> None:
    inspection = inspect_pdf(encrypt(make_pdf(["hi"]), ""), None, 1000)

    assert inspection.verdict is InspectionVerdict.OK
    assert inspection.decrypted is not None
    assert extract_text_pages(inspection.decrypted) == ["hi"]


def test_password_needed_wrong_and_right() -> None:
    locked = encrypt(make_pdf(["secret text"]), "pw-123")

    assert inspect_pdf(locked, None, 1000).verdict is InspectionVerdict.LOCKED
    assert inspect_pdf(locked, "", 1000).verdict is InspectionVerdict.LOCKED
    assert inspect_pdf(locked, "nope", 1000).verdict is InspectionVerdict.UNLOCK_FAILED
    opened = inspect_pdf(locked, "pw-123", 1000)
    assert opened.verdict is InspectionVerdict.OK
    assert opened.decrypted is not None
    assert b"/Encrypt" not in opened.decrypted
    assert extract_text_pages(opened.decrypted) == ["secret text"]


def test_garbage_is_unreadable() -> None:
    assert inspect_pdf(b"%PDF-1.4 nothing", None, 1000).verdict is InspectionVerdict.UNREADABLE


def test_split_23_pages_into_10_10_3() -> None:
    chunks = split_pdf(make_text_pdf(23), 10)

    assert [count for _, count in chunks] == [10, 10, 3]
    assert extract_text_pages(chunks[2][0]) == ["Page 21", "Page 22", "Page 23"]


def test_split_10_pages_is_one_chunk() -> None:
    assert [count for _, count in split_pdf(make_text_pdf(10), 10)] == [10]
