"""Keep a running job's claim fresh, so the reclaimer never steals live work (criterion 36)."""

import asyncio
import contextlib
from collections.abc import AsyncIterator

from app.core.logging import get_logger
from app.queue.job import Job
from app.queue.job_queue import JobQueue

log = get_logger("claim_keeper")


@contextlib.asynccontextmanager
async def keep_claim(queue: JobQueue, job: Job, every_s: float) -> AsyncIterator[None]:
    """Refresh the claim every ``every_s`` seconds while the block runs."""

    async def refresh_forever() -> None:
        while True:
            await asyncio.sleep(every_s)
            try:
                await queue.refresh(job)
            except Exception:  # noqa: BLE001 - a missed refresh is retried next tick
                log.warning("claim_refresh_failed", document_id=job.document_id)

    task = asyncio.create_task(refresh_forever())
    try:
        yield
    finally:
        task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await task
