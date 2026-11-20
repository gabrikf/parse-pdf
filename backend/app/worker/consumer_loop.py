"""The worker's loop: reclaim idle entries, read new ones, run one job at a time."""

import asyncio
import contextlib
import time
from dataclasses import dataclass

from app.core.logging import get_logger
from app.documents.use_cases.process_document import ProcessDocumentUseCase
from app.queue.job import Job
from app.queue.job_queue import JobQueue
from app.worker.claim_keeper import keep_claim

log = get_logger("consumer_loop")
READ_BLOCK_MS = 2_000
ERROR_PAUSE_S = 1.0


@dataclass(frozen=True, slots=True)
class LoopTiming:
    """Reclaim after ``claim_idle_ms`` idle, sweep every ``sweep_s``, refresh every
    ``refresh_s``, give a running job ``grace_s`` after a stop signal."""

    claim_idle_ms: int
    sweep_s: float
    refresh_s: float
    grace_s: float


class ConsumerLoop:
    """One job at a time, so a worker never runs two model calls at once.

    On stop it reads nothing new and gives the running job ``grace_s`` seconds; a job still
    running then is cancelled and stays pending, for another worker to reclaim.
    """

    def __init__(
        self, queue: JobQueue, process: ProcessDocumentUseCase, timing: LoopTiming
    ) -> None:
        self._queue = queue
        self._process = process
        self._timing = timing
        self._next_sweep = 0.0

    async def run(self, stop: asyncio.Event) -> None:
        """Consume until ``stop`` is set."""
        await self._queue.ensure_group()
        while not stop.is_set():
            try:
                job = await self._next_job()
            except Exception:
                log.exception("read_failed")
                await asyncio.sleep(ERROR_PAUSE_S)
                continue
            if job is not None:
                await self._run_with_grace(job, stop)

    async def _next_job(self) -> Job | None:
        if time.monotonic() >= self._next_sweep:
            self._next_sweep = time.monotonic() + self._timing.sweep_s
            reclaimed = await self._queue.reclaim(self._timing.claim_idle_ms)
            if reclaimed is not None:
                log.info("job_reclaimed", document_id=reclaimed.document_id)
                return reclaimed
        return await self._queue.read(READ_BLOCK_MS)

    async def _run_with_grace(self, job: Job, stop: asyncio.Event) -> None:
        task = asyncio.create_task(self._run(job))
        stopped = asyncio.create_task(stop.wait())
        await asyncio.wait({task, stopped}, return_when=asyncio.FIRST_COMPLETED)

        if not task.done():
            log.info("stop_requested", document_id=job.document_id)
            await asyncio.wait({task}, timeout=self._timing.grace_s)
        if not task.done():
            log.warning("job_left_for_reclaim", document_id=job.document_id)
            task.cancel()
        stopped.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await task

    async def _run(self, job: Job) -> None:
        async with keep_claim(self._queue, job, self._timing.refresh_s):
            try:
                await self._process.execute(job)
            except Exception:
                log.exception("job_crashed", document_id=job.document_id)
