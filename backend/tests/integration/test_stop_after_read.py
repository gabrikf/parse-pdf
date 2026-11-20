"""Criterion 40: a stop signal that lands while the worker waits on the stream starts no job."""

import asyncio

import httpx
from redis.asyncio import Redis
from types_aiobotocore_s3 import S3Client

from app.core.settings import Settings
from app.queue.job import CONSUMER_GROUP, STREAM_KEY, DeadLetter, Job
from app.queue.job_queue import JobQueue
from app.worker.consumer_loop import ConsumerLoop, LoopTiming
from tests.fakes import FakeChat
from tests.integration.harness import pdf_part, upload
from tests.integration.worker_parts import build_worker
from tests.pdf_factory import make_pdf


class StopDuringRead:
    """A queue whose read returns an entry only after the stop signal was set (SIGTERM mid-read)."""

    def __init__(self, queue: JobQueue, stop: asyncio.Event) -> None:
        self._queue = queue
        self._stop = stop

    async def ensure_group(self) -> None:
        """Delegate."""
        await self._queue.ensure_group()

    async def read(self, block_ms: int) -> Job | None:
        """Read, and set the stop signal before the entry is handed back."""
        job = await self._queue.read(block_ms)
        if job is not None:
            self._stop.set()
        return job

    async def reclaim(self, min_idle_ms: int) -> Job | None:
        """Never reclaim here, so the read is the path under test."""
        del min_idle_ms
        return None

    async def refresh(self, job: Job) -> None:
        """Delegate."""
        await self._queue.refresh(job)

    async def ack(self, job: Job) -> None:
        """Delegate."""
        await self._queue.ack(job)

    async def dead_letter(self, letter: DeadLetter) -> None:
        """Delegate."""
        await self._queue.dead_letter(letter)


async def test_entry_read_after_the_stop_signal_stays_pending_with_no_calls(
    session_client: httpx.AsyncClient, redis: Redis, s3: S3Client, settings: Settings
) -> None:
    response = await upload(
        session_client,
        [pdf_part("a.pdf", make_pdf(["alpha"])), pdf_part("b.pdf", make_pdf(["beta"]))],
    )
    assert response.status_code == 202
    ids = [str(item["id"]) for item in response.json()["data"]["documents"]]
    chat = FakeChat()
    parts = build_worker(redis, s3, settings, chat)
    stop = asyncio.Event()
    queue = StopDuringRead(parts.queue, stop)
    timing = LoopTiming(claim_idle_ms=60_000, sweep_s=15, refresh_s=20, grace_s=30)

    await asyncio.wait_for(ConsumerLoop(queue, parts.process, timing).run(stop), timeout=5)

    assert chat.calls == []
    assert [await redis.hget(f"doc:{doc_id}", "status") for doc_id in ids] == ["queued", "queued"]
    assert (await redis.xpending(STREAM_KEY, CONSUMER_GROUP))["pending"] == 1
