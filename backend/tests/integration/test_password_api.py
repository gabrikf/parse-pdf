"""Criteria 51-53: encrypted PDFs, the password rules, and the password never kept."""

import io
import logging

import httpx
import pytest
from pypdf import PdfReader
from redis.asyncio import Redis
from types_aiobotocore_s3 import S3Client

from app.core.settings import Settings
from tests.fakes import FakeChat
from tests.integration.harness import pdf_part, upload
from tests.integration.worker_parts import build_worker
from tests.pdf_factory import encrypt, make_pdf

PASSWORD = "Tr0ub4dor-literal-7731"


async def _object_count(s3: S3Client, settings: Settings) -> int:
    listed = await s3.list_objects_v2(Bucket=settings.s3_bucket)
    return int(listed.get("KeyCount", 0))


async def test_empty_password_pdf_is_accepted_like_any_pdf(
    session_client: httpx.AsyncClient,
) -> None:
    locked = encrypt(make_pdf(["open"]), user_password="")

    response = await upload(session_client, [pdf_part("open.pdf", locked)])

    assert response.status_code == 202, response.text
    assert response.json()["data"]["documents"][0]["status"] == "queued"


@pytest.mark.parametrize(
    ("password", "code"),
    [(None, "password_required"), ("", "password_required"), ("nope", "wrong_password")],
)
async def test_missing_or_wrong_password_is_rejected_and_nothing_stored(
    session_client: httpx.AsyncClient,
    redis: Redis,
    s3: S3Client,
    settings: Settings,
    password: str | None,
    code: str,
) -> None:
    locked = encrypt(make_pdf(["secret"]), user_password=PASSWORD)
    before = await _object_count(s3, settings)
    extra = {} if password is None else {"password": password}

    response = await upload(session_client, [pdf_part("locked.pdf", locked)], **extra)

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "all_files_rejected"
    rejected = response.json()["error"]["details"]["rejected"]
    assert [item["code"] for item in rejected] == [code]
    assert await _object_count(s3, settings) == before
    assert [key async for key in redis.scan_iter(match="doc:*")] == []


async def test_right_password_stores_decrypted_bytes_and_never_the_password(
    session_client: httpx.AsyncClient,
    redis: Redis,
    s3: S3Client,
    settings: Settings,
    capfd: pytest.CaptureFixture[str],
    caplog: pytest.LogCaptureFixture,
) -> None:
    caplog.set_level(logging.DEBUG)
    locked = encrypt(make_pdf(["first"]), user_password=PASSWORD)
    other = encrypt(make_pdf(["second"]), user_password=PASSWORD)

    response = await upload(
        session_client,
        [pdf_part("a.pdf", locked), pdf_part("b.pdf", other)],
        password=PASSWORD,
    )
    parts = build_worker(redis, s3, settings, FakeChat())
    await parts.queue.ensure_group()
    for _ in range(2):
        job = await parts.queue.read(block_ms=100)
        assert job is not None
        await parts.process.execute(job)

    assert response.status_code == 202, response.text
    assert PASSWORD not in response.text
    documents = response.json()["data"]["documents"]
    assert len(documents) == 2
    for document in documents:
        key = f"documents/{document['id']}.pdf"
        stored = await (await s3.get_object(Bucket=settings.s3_bucket, Key=key))["Body"].read()
        assert PdfReader(io.BytesIO(stored)).is_encrypted is False
        assert PASSWORD.encode() not in stored
        read = await session_client.get(f"/api/v1/documents/{document['id']}")
        assert read.json()["data"]["status"] == "ready"
        assert PASSWORD not in read.text
    dumps = [await redis.dump(key) async for key in redis.scan_iter()]
    assert dumps
    assert all(PASSWORD.encode() not in (dump or b"") for dump in dumps)
    logged = capfd.readouterr()
    assert PASSWORD not in logged.out + logged.err
    assert PASSWORD not in caplog.text
