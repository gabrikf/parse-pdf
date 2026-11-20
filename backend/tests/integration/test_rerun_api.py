"""Criteria 47-50: reparse, requeue and delete, with their guards."""

import asyncio
from typing import cast

import httpx
import pytest
from redis.asyncio import Redis
from types_aiobotocore_s3 import S3Client

from app.core.settings import Settings
from app.documents.domain.document_status import DocumentStatus
from app.queue.job import STREAM_KEY
from tests.integration.seed import seed


async def _session_id(client: httpx.AsyncClient) -> str:
    response = await client.post("/api/v1/sessions")
    session_id: str = response.json()["data"]["session_id"]
    return session_id


async def _entries(redis: Redis) -> list[dict[str, str]]:
    entries = cast("list[tuple[str, dict[str, str]]]", await redis.xrange(STREAM_KEY))
    return [fields for _, fields in entries]


async def _clear_stream(redis: Redis) -> None:
    await redis.delete(STREAM_KEY)


@pytest.mark.parametrize(
    "status", [DocumentStatus.READY, DocumentStatus.NO_TEXT, DocumentStatus.DEAD]
)
async def test_reparse_a_final_document_queues_a_new_run_with_cleared_results(
    session_client: httpx.AsyncClient, redis: Redis, status: DocumentStatus
) -> None:
    document = await seed(redis, await _session_id(session_client), 0, status, pages=["a", "b"])
    await redis.hset(f"doc:{document.id}:chunks", "0", "[]")
    await _clear_stream(redis)

    response = await session_client.post(
        f"/api/v1/documents/{document.id}/reparse", json={"parser": "gemini-3.1-flash-lite"}
    )

    assert response.status_code == 202, response.text
    record = await redis.hgetall(f"doc:{document.id}")
    assert record["status"] == "queued"
    assert record["parser"] == "gemini-3.1-flash-lite"
    assert record["run_id"] != document.run_id
    assert record.get("summary", "") == ""
    assert await redis.exists(f"doc:{document.id}:pages", f"doc:{document.id}:chunks") == 0
    assert await _entries(redis) == [
        {
            "document_id": document.id,
            "object_key": document.object_key,
            "run_id": record["run_id"],
        }
    ]


async def test_two_concurrent_reparses_give_one_202_and_one_409(
    session_client: httpx.AsyncClient, redis: Redis
) -> None:
    document = await seed(redis, await _session_id(session_client), 0, DocumentStatus.READY)
    await _clear_stream(redis)
    url = f"/api/v1/documents/{document.id}/reparse"

    first, second = await asyncio.gather(
        session_client.post(url, json={"parser": "pypdf"}),
        session_client.post(url, json={"parser": "pypdf"}),
    )

    assert sorted([first.status_code, second.status_code]) == [202, 409]
    loser = first if first.status_code == 409 else second
    assert loser.json()["error"]["code"] == "document_busy"
    assert await redis.xlen(STREAM_KEY) == 1


@pytest.mark.parametrize("status", [DocumentStatus.QUEUED, DocumentStatus.PROCESSING])
@pytest.mark.parametrize("action", ["reparse", "requeue"])
async def test_busy_documents_refuse_reparse_and_requeue(
    session_client: httpx.AsyncClient, redis: Redis, status: DocumentStatus, action: str
) -> None:
    document = await seed(redis, await _session_id(session_client), 0, status)

    response = await session_client.post(
        f"/api/v1/documents/{document.id}/{action}", json={"parser": "pypdf"}
    )

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "document_busy"


async def test_reparse_too_large_is_not_reparsable(
    session_client: httpx.AsyncClient, redis: Redis
) -> None:
    document = await seed(redis, await _session_id(session_client), 0, DocumentStatus.TOO_LARGE)

    response = await session_client.post(
        f"/api/v1/documents/{document.id}/reparse", json={"parser": "pypdf"}
    )

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "not_reparsable"


@pytest.mark.parametrize("parser", [None, "", "PyPDF"])
async def test_reparse_with_a_bad_parser_is_422(
    session_client: httpx.AsyncClient, redis: Redis, parser: str | None
) -> None:
    document = await seed(redis, await _session_id(session_client), 0, DocumentStatus.READY)

    response = await session_client.post(
        f"/api/v1/documents/{document.id}/reparse", json={"parser": parser}
    )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "invalid_parser"


async def test_requeue_a_dead_document_keeps_its_parser(
    session_client: httpx.AsyncClient, redis: Redis
) -> None:
    document = await seed(redis, await _session_id(session_client), 0, DocumentStatus.DEAD)
    await _clear_stream(redis)

    response = await session_client.post(f"/api/v1/documents/{document.id}/requeue")

    assert response.status_code == 202, response.text
    record = await redis.hgetall(f"doc:{document.id}")
    assert record["status"] == "queued"
    assert record["parser"] == "pypdf"
    assert record.get("error_code", "") == ""
    assert [entry["run_id"] for entry in await _entries(redis)] == [record["run_id"]]


@pytest.mark.parametrize(
    "status", [DocumentStatus.READY, DocumentStatus.NO_TEXT, DocumentStatus.TOO_LARGE]
)
async def test_requeue_a_document_that_is_not_dead_is_409(
    session_client: httpx.AsyncClient, redis: Redis, status: DocumentStatus
) -> None:
    document = await seed(redis, await _session_id(session_client), 0, status)

    response = await session_client.post(f"/api/v1/documents/{document.id}/requeue")

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "not_dead"


async def test_delete_removes_record_pages_chunks_feed_and_object(
    session_client: httpx.AsyncClient, redis: Redis, s3: S3Client, settings: Settings
) -> None:
    session_id = await _session_id(session_client)
    document = await seed(redis, session_id, 0, DocumentStatus.READY, pages=["a"])
    key = document.object_key or ""
    await s3.put_object(Bucket=settings.s3_bucket, Key=key, Body=b"%PDF-1.4")

    response = await session_client.delete(f"/api/v1/documents/{document.id}")

    assert response.status_code == 200
    assert response.json()["data"] == {"id": document.id, "deleted": True}
    assert [key async for key in redis.scan_iter(match=f"doc:{document.id}*")] == []
    for group in ["", ":parsed", ":failed", ":active"]:
        assert await redis.zscore(f"session:{session_id}:docs{group}", document.id) is None
    listed = await s3.list_objects_v2(Bucket=settings.s3_bucket, Prefix=key)
    assert listed.get("KeyCount", 0) == 0
    after = await session_client.get(f"/api/v1/documents/{document.id}")
    assert after.status_code == 404


async def test_delete_a_processing_document_is_409(
    session_client: httpx.AsyncClient, redis: Redis
) -> None:
    document = await seed(redis, await _session_id(session_client), 0, DocumentStatus.PROCESSING)

    response = await session_client.delete(f"/api/v1/documents/{document.id}")

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "document_busy"
    assert await redis.hget(f"doc:{document.id}", "status") == "processing"


async def test_delete_a_queued_document_is_200(
    session_client: httpx.AsyncClient, redis: Redis
) -> None:
    document = await seed(redis, await _session_id(session_client), 0, DocumentStatus.QUEUED)

    response = await session_client.delete(f"/api/v1/documents/{document.id}")

    assert response.status_code == 200
    assert await redis.exists(f"doc:{document.id}") == 0
