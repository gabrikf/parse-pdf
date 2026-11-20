"""Write a timestamp every few seconds; the Compose healthcheck reads its age (criterion 41)."""

import asyncio
import os
import time
from pathlib import Path

from app.core.settings import DEFAULT_HEARTBEAT_PATH

STALE_AFTER_S = 30.0


async def beat_forever(path: Path, every_s: float) -> None:
    """Write the current time to ``path`` until cancelled.

    The beat runs on the event loop, so a blocked loop stops it and the worker turns unhealthy.
    """
    while True:
        await asyncio.to_thread(path.write_text, f"{time.time():.3f}")
        await asyncio.sleep(every_s)


def is_fresh(path: Path, now: float, stale_after_s: float = STALE_AFTER_S) -> bool:
    """True when the last beat is younger than ``stale_after_s`` seconds."""
    try:
        return now - float(path.read_text()) < stale_after_s
    except (OSError, ValueError):
        return False


def main() -> int:
    """Healthcheck entry point: exit 0 when the heartbeat is fresh, 1 otherwise."""
    path = Path(os.environ.get("HEARTBEAT_PATH", DEFAULT_HEARTBEAT_PATH))
    return 0 if is_fresh(path, time.time()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
