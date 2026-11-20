"""Criteria 36, 37, 38 and 40 with in-process consumer loops on the real Redis and bucket."""

import asyncio
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import cast

import httpx
import pytest
from redis.asyncio import Redis
from types_aiobotocore_s3 import S3Client

from app.core.settings import Settings
from app.models.chat_model import ChatRequest
from app.queue.job import CONSUMER_GROUP, DEAD_LETTER_KEY, STREAM_KEY
from app.worker.consumer_loop import ConsumerLoop, LoopTiming
from tests.fakes import FakeChat
from tests.integration.harness import pdf_part, upload
from tests.integration.worker_parts import build_worker
from tests.pdf_factory import make_pdf


@dataclass
class SlowChat(FakeChat):
    """A chat model whose every call takes ``delay_s``."""

    delay_s: float = 0.0

    async def complete(self, request: ChatRequest) -> str:
        await asyncio.sleep(self.delay_s)
        return await super().complete(request)


async def _upload(client: httpx.AsyncClient) -> str:
    response = await upload(client, [pdf_part("a.pdf", make_pdf(["alpha"]))])
    assert response.status_code == 202
    return str(response.json()["data"]["documents"][0]["id"])


async def _status(redis: Redis, document_id: str) -> str | None:
    value = await redis.hget(f"doc:{document_id}", "status")
    return None if value is None else str(value)


async def _wait_for(redis: Redis, document_id: str, status: str, seconds: float = 10) -> None:
    for _ in range(int(seconds / 0.02)):
        if await _status(redis, document_id) == status:
            return
        await asyncio.sleep(0.02)
    raise AssertionError(f"{document_id} never reached {status}")


async def test_claim_refresh_keeps_a_long_job_on_one_worker(
    session_client: httpx.AsyncClient, redis: Redis, s3: S3Client, settings: Settings
) -> None:
    document_id = await _upload(session_client)
    timing = LoopTiming(claim_idle_ms=600, sweep_s=0.1, refresh_s=0.2, grace_s=5)
    chats = [SlowChat(delay_s=0.7), SlowChat(delay_s=0.7)]
    loops = [
        ConsumerLoop(parts.queue, parts.process, timing)
        for parts in (
            build_worker(redis, s3, settings, chats[0], consumer="w1"),
            build_worker(redis, s3, settings, chats[1], consumer="w2"),
        )
    ]
    stop = asyncio.Event()
    tasks = [asyncio.create_task(loop.run(stop)) for loop in loops]

    for _ in range(100):
        if await _status(redis, document_id) == "ready":
            break
        await asyncio.sleep(0.1)
    stop.set()
    await asyncio.gather(*tasks)

    assert await _status(redis, document_id) == "ready"
    assert await redis.hget(f"doc:{document_id}", "deliveries") == "1"
    assert sorted(len(chat.calls) for chat in chats) == [0, 3]


async def test_idle_entry_is_reclaimed_by_another_worker(
    session_client: httpx.AsyncClient, redis: Redis, s3: S3Client, settings: Settings
) -> None:
    document_id = await _upload(session_client)
    crashed = build_worker(redis, s3, settings, FakeChat(), consumer="crashed")
    await crashed.queue.ensure_group()
    assert await crashed.queue.read(block_ms=100) is not None
    run_id = str(await redis.hget(f"doc:{document_id}", "run_id") or "")
    await crashed.repository.begin_run(document_id, run_id, 5, datetime.now(UTC))
    survivor = build_worker(redis, s3, settings, FakeChat(), consumer="survivor")
    timing = LoopTiming(claim_idle_ms=300, sweep_s=0.05, refresh_s=1, grace_s=5)
    stop = asyncio.Event()
    task = asyncio.create_task(ConsumerLoop(survivor.queue, survivor.process, timing).run(stop))

    for _ in range(60):
        if await _status(redis, document_id) == "ready":
            break
        await asyncio.sleep(0.1)
    stop.set()
    await task

    assert await _status(redis, document_id) == "ready"
    assert await redis.hget(f"doc:{document_id}", "deliveries") == "2"
    assert (await redis.xpending(STREAM_KEY, CONSUMER_GROUP))["pending"] == 0


@pytest.mark.parametrize(("previous", "status"), [(4, "ready"), (5, "dead")])
async def test_sixth_delivery_is_dead_letter_with_no_calls(
    session_client: httpx.AsyncClient,
    redis: Redis,
    s3: S3Client,
    settings: Settings,
    previous: int,
    status: str,
) -> None:
    document_id = await _upload(session_client)
    await redis.hset(f"doc:{document_id}", "deliveries", previous)
    chat = FakeChat()
    parts = build_worker(redis, s3, settings, chat)
    await parts.queue.ensure_group()
    job = await parts.queue.read(block_ms=100)
    assert job is not None

    await parts.process.execute(job)

    assert await _status(redis, document_id) == status
    assert await redis.xlen(STREAM_KEY) == 0
    if status == "dead":
        assert chat.calls == []
        assert await redis.hget(f"doc:{document_id}", "error_code") == "max_deliveries"
        letters = cast("list[tuple[str, dict[str, str]]]", await redis.xrange(DEAD_LETTER_KEY))
        ((_, letter),) = letters
        assert letter == {
            "document_id": document_id,
            "run_id": job.run_id,
            "error_code": "max_deliveries",
            "deliveries": "6",
        }
        failed = await session_client.get("/api/v1/documents", params={"state": "failed"})
        assert [d["id"] for d in failed.json()["data"]] == [document_id]
    else:
        assert len(chat.calls) == 3


async def test_stop_signal_lets_the_running_job_finish(
    session_client: httpx.AsyncClient, redis: Redis, s3: S3Client, settings: Settings
) -> None:
    document_id = await _upload(session_client)
    parts = build_worker(redis, s3, settings, SlowChat(delay_s=0.3))
    timing = LoopTiming(claim_idle_ms=60_000, sweep_s=15, refresh_s=20, grace_s=30)
    stop = asyncio.Event()
    task = asyncio.create_task(ConsumerLoop(parts.queue, parts.process, timing).run(stop))
    await _wait_for(redis, document_id, "processing")

    stop.set()
    await asyncio.wait_for(task, timeout=10)

    assert await _status(redis, document_id) == "ready"


async def test_job_past_the_grace_stays_pending_for_reclaim(
    session_client: httpx.AsyncClient, redis: Redis, s3: S3Client, settings: Settings
) -> None:
    document_id = await _upload(session_client)
    parts = build_worker(redis, s3, settings, SlowChat(delay_s=5))
    timing = LoopTiming(claim_idle_ms=60_000, sweep_s=15, refresh_s=20, grace_s=0.3)
    stop = asyncio.Event()
    task = asyncio.create_task(ConsumerLoop(parts.queue, parts.process, timing).run(stop))
    await _wait_for(redis, document_id, "processing")

    stop.set()
    await asyncio.wait_for(task, timeout=5)

    assert await _status(redis, document_id) == "processing"
    assert (await redis.xpending(STREAM_KEY, CONSUMER_GROUP))["pending"] == 1
