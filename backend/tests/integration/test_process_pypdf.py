"""Criteria 11, 12, 23, 38 and 39: pypdf jobs; stale and final entries are skipped."""

import httpx
from redis.asyncio import Redis
from types_aiobotocore_s3 import S3Client

from app.core.settings import Settings
from app.documents.use_cases.process_document import JobOutcome
from app.queue.job import CONSUMER_GROUP, STREAM_KEY
from tests.fakes import FakeChat
from tests.integration.harness import pdf_part, upload
from tests.integration.worker_parts import WorkerParts, build_worker
from tests.pdf_factory import make_pdf


async def _upload_one(client: httpx.AsyncClient, pdf: bytes) -> dict[str, str]:
    response = await upload(client, [pdf_part("doc.pdf", pdf)])
    assert response.status_code == 202, response.text
    document: dict[str, str] = response.json()["data"]["documents"][0]
    return document


async def _work_once(parts: WorkerParts) -> JobOutcome:
    await parts.queue.ensure_group()
    job = await parts.queue.read(block_ms=100)
    assert job is not None
    return await parts.process.execute(job)


async def test_upload_returns_queued_before_any_worker_runs(
    session_client: httpx.AsyncClient, redis: Redis
) -> None:
    document = await _upload_one(session_client, make_pdf(["hello"]))

    assert document["status"] == "queued"
    groups = await redis.xinfo_groups(STREAM_KEY) if await redis.exists(STREAM_KEY) else []
    assert all(group["pel-count"] == 0 for group in groups)


async def test_pypdf_job_ends_ready_with_text_pages_in_order(
    session_client: httpx.AsyncClient, redis: Redis, s3: S3Client, settings: Settings
) -> None:
    document = await _upload_one(session_client, make_pdf(["alpha", "beta", "gamma"]))
    chat = FakeChat()

    outcome = await _work_once(build_worker(redis, s3, settings, chat))

    assert outcome is JobOutcome.ACKED
    read = (await session_client.get(f"/api/v1/documents/{document['id']}")).json()["data"]
    assert read["status"] == "ready"
    assert read["summary"].startswith("## Overview")
    pages = (await session_client.get(f"/api/v1/documents/{document['id']}/pages")).json()
    assert pages["data"] == [
        {"number": 1, "content": "alpha", "format": "text"},
        {"number": 2, "content": "beta", "format": "text"},
        {"number": 3, "content": "gamma", "format": "text"},
    ]
    assert await redis.xlen(STREAM_KEY) == 0
    pending = await redis.xpending(STREAM_KEY, CONSUMER_GROUP)
    assert pending["pending"] == 0
    assert await redis.hget(f"doc:{document['id']}", "deliveries") == "1"


async def test_all_blank_pages_end_no_text_with_gemini_hint(
    session_client: httpx.AsyncClient, redis: Redis, s3: S3Client, settings: Settings
) -> None:
    document = await _upload_one(session_client, make_pdf(["", "", ""]))
    chat = FakeChat()

    await _work_once(build_worker(redis, s3, settings, chat))

    read = (await session_client.get(f"/api/v1/documents/{document['id']}")).json()["data"]
    assert read["status"] == "no_text"
    assert "gemini-3.1-flash-lite" in read["hint"]
    assert read["summary"] is None
    assert chat.calls == []


async def test_one_character_on_page_2_of_3_is_not_no_text(
    session_client: httpx.AsyncClient, redis: Redis, s3: S3Client, settings: Settings
) -> None:
    document = await _upload_one(session_client, make_pdf(["", "x", ""]))

    await _work_once(build_worker(redis, s3, settings, FakeChat()))

    read = (await session_client.get(f"/api/v1/documents/{document['id']}")).json()["data"]
    assert read["status"] == "ready"


async def test_redelivered_final_run_is_acked_with_no_calls(
    session_client: httpx.AsyncClient, redis: Redis, s3: S3Client, settings: Settings
) -> None:
    document = await _upload_one(session_client, make_pdf(["alpha"]))
    first = build_worker(redis, s3, settings, FakeChat())
    await first.queue.ensure_group()
    job = await first.queue.read(block_ms=100)
    assert job is not None
    await first.process.execute(job)
    chat = FakeChat()

    again = build_worker(redis, s3, settings, chat)
    outcome = await again.process.execute(job)

    assert outcome is JobOutcome.ACKED
    assert chat.calls == []
    read = (await session_client.get(f"/api/v1/documents/{document['id']}")).json()["data"]
    assert read["status"] == "ready"


async def test_stale_run_and_deleted_document_are_dropped(
    session_client: httpx.AsyncClient, redis: Redis, s3: S3Client, settings: Settings
) -> None:
    kept = await _upload_one(session_client, make_pdf(["alpha"]))
    removed = await _upload_one(session_client, make_pdf(["beta"]))
    await redis.hset(f"doc:{kept['id']}", "run_id", "another-run")
    delete = await session_client.delete(f"/api/v1/documents/{removed['id']}")
    assert delete.status_code == 200
    chat = FakeChat()
    parts = build_worker(redis, s3, settings, chat)

    outcomes = [await _work_once(parts), await _work_once(parts)]

    assert outcomes == [JobOutcome.ACKED, JobOutcome.ACKED]
    assert chat.calls == []
    assert await redis.hget(f"doc:{kept['id']}", "status") == "queued"
    assert await redis.xlen(STREAM_KEY) == 0
