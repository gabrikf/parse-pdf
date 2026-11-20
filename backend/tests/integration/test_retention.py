"""Criterion 25: every key lives 7 days, refreshed on each status change; the bucket expires."""

from datetime import UTC, datetime

import httpx
from redis.asyncio import Redis
from types_aiobotocore_s3 import S3Client

from app.core.settings import Settings
from app.repositories.redis_document_repository import RedisDocumentRepository
from tests.integration.harness import pdf_part, upload
from tests.pdf_factory import make_pdf

WEEK_S = 604_800


async def _document_and_session_keys(redis: Redis) -> list[str]:
    keys = [str(key) async for key in redis.scan_iter(match="doc:*")]
    keys += [str(key) async for key in redis.scan_iter(match="session:*")]
    return keys


async def test_every_doc_and_session_key_gets_a_week(
    session_client: httpx.AsyncClient, redis: Redis
) -> None:
    await upload(session_client, [pdf_part("a.pdf", make_pdf(["alpha"]))])

    keys = await _document_and_session_keys(redis)

    assert any(key.startswith("doc:") for key in keys)
    assert any(key.startswith("session:") for key in keys)
    for key in keys:
        assert WEEK_S - 5 <= await redis.ttl(key) <= WEEK_S, key


async def test_a_status_change_refreshes_the_ttl(
    session_client: httpx.AsyncClient, redis: Redis
) -> None:
    response = await upload(session_client, [pdf_part("a.pdf", make_pdf(["alpha"]))])
    document_id = response.json()["data"]["documents"][0]["id"]
    for key in await _document_and_session_keys(redis):
        await redis.expire(key, 100)
    run_id = str(await redis.hget(f"doc:{document_id}", "run_id"))

    await RedisDocumentRepository(redis).begin_run(document_id, run_id, 5, datetime.now(UTC))

    assert await redis.hget(f"doc:{document_id}", "status") == "processing"
    for key in await _document_and_session_keys(redis):
        assert await redis.ttl(key) >= WEEK_S - 5, key


async def test_bucket_expires_objects_after_7_days(
    session_client: httpx.AsyncClient, s3: S3Client, settings: Settings
) -> None:
    del session_client

    rules = (await s3.get_bucket_lifecycle_configuration(Bucket=settings.s3_bucket))["Rules"]

    assert [rule.get("Expiration", {}).get("Days") for rule in rules] == [7]
    assert rules[0]["Status"] == "Enabled"
