"""Criteria 5-10 and 26: what an upload accepts, refuses, stores and queues."""

from collections.abc import AsyncIterator

import httpx
import pytest
from redis.asyncio import Redis

from app.core.settings import Settings
from app.queue.job import STREAM_KEY
from tests.integration.harness import open_session, pdf_part, upload
from tests.integration.storage_probe import bucket_client, object_bytes, object_exists
from tests.pdf_factory import PNG_BYTES, make_text_pdf

ONE_PAGE = make_text_pdf(1)


async def _stream_entries(redis: Redis) -> list[dict[str, str]]:
    entries: list[tuple[str, dict[str, str]]] = await redis.xrange(STREAM_KEY)  # type: ignore[assignment]
    return [fields for _, fields in entries]


async def test_upload_queues_each_file_in_order_and_stores_it(
    session_client: httpx.AsyncClient, redis: Redis, settings: Settings
) -> None:
    names = [f"file-{index}.pdf" for index in range(3)]
    response = await upload(session_client, [pdf_part(n, ONE_PAGE) for n in names])

    assert response.status_code == 202
    documents = response.json()["data"]["documents"]
    assert [d["filename"] for d in documents] == names
    assert {d["status"] for d in documents} == {"queued"}
    assert response.json()["data"]["rejected"] == []

    entries = await _stream_entries(redis)
    assert len(entries) == 3
    assert {tuple(sorted(entry)) for entry in entries} == {("document_id", "object_key", "run_id")}
    assert sorted(e["document_id"] for e in entries) == sorted(d["id"] for d in documents)
    async with bucket_client(settings) as s3:
        for document in documents:
            key = f"documents/{document['id']}.pdf"
            assert await object_bytes(s3, settings.s3_bucket, key) == ONE_PAGE


@pytest.mark.parametrize(
    "parser",
    [None, "", "PyPDF", "gpt5mini"],
    ids=["omitted", "empty", "PyPDF", "gpt5mini"],
)
async def test_unknown_parser_is_422_and_stores_nothing(
    session_client: httpx.AsyncClient, redis: Redis, parser: str | None
) -> None:
    response = await upload(session_client, [pdf_part("a.pdf", ONE_PAGE)], parser=parser)

    assert response.status_code == 422
    error = response.json()["error"]
    assert error["code"] == "invalid_parser"
    assert error["details"]["allowed"] == ["pypdf", "gemini-3.1-flash-lite", "gpt-5-mini"]
    assert await _stream_entries(redis) == []


async def test_no_files_is_422(session_client: httpx.AsyncClient) -> None:
    response = await session_client.post("/api/v1/documents", data={"parser": "pypdf"})

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "no_files"


async def test_20_files_are_accepted(session_client: httpx.AsyncClient) -> None:
    response = await upload(session_client, [pdf_part(f"{i}.pdf", ONE_PAGE) for i in range(20)])

    assert response.status_code == 202
    assert len(response.json()["data"]["documents"]) == 20


async def test_21_files_are_422_and_store_nothing(
    session_client: httpx.AsyncClient, redis: Redis
) -> None:
    response = await upload(session_client, [pdf_part(f"{i}.pdf", ONE_PAGE) for i in range(21)])

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "too_many_files"
    assert await _stream_entries(redis) == []
    assert await redis.keys("doc:*") == []


async def test_bad_files_are_rejected_beside_good_ones(
    session_client: httpx.AsyncClient,
) -> None:
    files = [
        pdf_part("scan.pdf", PNG_BYTES),
        pdf_part("report.txt", ONE_PAGE),
        pdf_part("good.pdf", ONE_PAGE),
    ]
    response = await upload(session_client, files)

    assert response.status_code == 202
    data = response.json()["data"]
    assert [d["filename"] for d in data["documents"]] == ["report.txt", "good.pdf"]
    assert data["rejected"] == [
        {"filename": "scan.pdf", "code": "not_pdf", "message": "The file is not a PDF."}
    ]


async def test_all_bad_files_is_422_all_files_rejected(
    session_client: httpx.AsyncClient, redis: Redis
) -> None:
    files = [
        pdf_part("empty.pdf", b""),
        pdf_part("scan.pdf", PNG_BYTES),
        pdf_part("broken.pdf", b"%PDF-1.4\n garbage without objects"),
    ]
    response = await upload(session_client, files)

    assert response.status_code == 422
    error = response.json()["error"]
    assert error["code"] == "all_files_rejected"
    codes = [r["code"] for r in error["details"]["rejected"]]
    assert codes == ["empty", "not_pdf", "unreadable_pdf"]
    assert await redis.keys("doc:*") == []


async def test_signature_after_first_1024_bytes_is_not_pdf(
    session_client: httpx.AsyncClient,
) -> None:
    late = b" " * 1024 + ONE_PAGE
    response = await upload(session_client, [pdf_part("late.pdf", late)])

    assert response.status_code == 422
    assert response.json()["error"]["details"]["rejected"][0]["code"] == "not_pdf"


@pytest.mark.parametrize(("size", "status"), [(52_428_800, "queued"), (52_428_801, "too_large")])
async def test_size_boundary(
    session_client: httpx.AsyncClient, redis: Redis, settings: Settings, size: int, status: str
) -> None:
    data = ONE_PAGE + b"\n%" + b"0" * (size - len(ONE_PAGE) - 2)
    response = await upload(session_client, [pdf_part("big.pdf", data)])

    assert response.status_code == 202
    document = response.json()["data"]["documents"][0]
    assert document["status"] == status
    assert document["size_bytes"] == size
    key = f"documents/{document['id']}.pdf"
    async with bucket_client(settings) as s3:
        assert await object_exists(s3, settings.s3_bucket, key) is (status == "queued")
    assert len(await _stream_entries(redis)) == (1 if status == "queued" else 0)


@pytest.mark.parametrize(("pages", "status"), [(1000, "queued"), (1001, "too_large")])
async def test_page_boundary(
    session_client: httpx.AsyncClient, redis: Redis, pages: int, status: str
) -> None:
    response = await upload(session_client, [pdf_part("long.pdf", make_text_pdf(pages))])

    assert response.status_code == 202
    document = response.json()["data"]["documents"][0]
    assert document["status"] == status
    assert document["page_count"] == pages
    assert len(await _stream_entries(redis)) == (1 if status == "queued" else 0)


async def test_body_over_limit_is_413_whatever_content_length_says(
    session_client: httpx.AsyncClient,
) -> None:
    declared = {"content-length": "100", "content-type": "multipart/form-data; boundary=xyz"}
    head = (
        b'--xyz\r\nContent-Disposition: form-data; name="files"; filename="big.pdf"\r\n'
        b"Content-Type: application/pdf\r\n\r\n%PDF-1.4\n"
    )
    chunk = b"x" * 1_048_576

    async def endless() -> AsyncIterator[bytes]:
        yield head
        for _ in range(1100):
            yield chunk

    request = session_client.build_request(
        "POST", "/api/v1/documents", content=endless(), headers=declared
    )
    response = await session_client.send(request)

    assert response.status_code == 413
    assert response.json()["error"]["code"] == "request_too_large"


async def test_declared_length_over_limit_is_413(session_client: httpx.AsyncClient) -> None:
    headers = {"content-length": str(1_074_790_401), "content-type": "multipart/form-data; b=x"}
    request = session_client.build_request(
        "POST", "/api/v1/documents", content=b"", headers=headers
    )
    response = await session_client.send(request)

    assert response.status_code == 413


async def test_filename_is_cleaned_and_never_the_key(
    session_client: httpx.AsyncClient, redis: Redis
) -> None:
    response = await upload(session_client, [pdf_part("../../etc/passwd.pdf", ONE_PAGE)])

    document = response.json()["data"]["documents"][0]
    assert document["filename"] == "passwd.pdf"
    entry = (await _stream_entries(redis))[0]
    assert entry["object_key"] == f"documents/{document['id']}.pdf"


async def test_11th_upload_in_60s_is_429_rate_limited(session_client: httpx.AsyncClient) -> None:
    for _ in range(10):
        assert (await upload(session_client, [pdf_part("a.pdf", ONE_PAGE)])).status_code == 202

    response = await upload(session_client, [pdf_part("a.pdf", ONE_PAGE)])

    assert response.status_code == 429
    assert response.json()["error"]["code"] == "rate_limited"
    assert int(response.headers["Retry-After"]) >= 1


async def test_third_upload_in_flight_is_429(client: httpx.AsyncClient, redis: Redis) -> None:
    await open_session(client)
    session_id = (await client.post("/api/v1/sessions")).json()["data"]["session_id"]
    await redis.set(f"inflight:upload:{session_id}", 2)

    response = await upload(client, [pdf_part("a.pdf", ONE_PAGE)])

    assert response.status_code == 429
    assert response.json()["error"]["code"] == "too_many_uploads_in_progress"
    await redis.set(f"inflight:upload:{session_id}", 1)
    assert (await upload(client, [pdf_part("a.pdf", ONE_PAGE)])).status_code == 202
    assert await redis.get(f"inflight:upload:{session_id}") == "1"
