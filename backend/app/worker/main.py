"""Worker process entry point: ``python -m app.worker.main``."""

import asyncio
import contextlib
from pathlib import Path

from app.core.logging import configure_logging, get_logger
from app.core.settings import get_settings
from app.worker.heartbeat import beat_forever
from app.worker.shutdown import install_stop_signals
from app.worker_container import worker_loop


async def run() -> None:
    """Consume until SIGTERM, beating the heartbeat all along."""
    settings = get_settings()
    configure_logging(settings.log_level)
    log = get_logger("worker")

    stop = asyncio.Event()
    install_stop_signals(stop)
    beat = asyncio.create_task(
        beat_forever(Path(settings.heartbeat_path), settings.heartbeat_interval_s)
    )
    try:
        async with worker_loop(settings) as loop:
            log.info("worker_started")
            await loop.run(stop)
    finally:
        beat.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await beat
        log.info("worker_stopped")


if __name__ == "__main__":
    asyncio.run(run())
