"""Port: the consumer side of the Redis Streams queue."""

from typing import Protocol

from app.queue.job import DeadLetter, Job


class JobQueue(Protocol):
    """Read, reclaim, keep and acknowledge jobs for one consumer."""

    async def ensure_group(self) -> None:
        """Create the stream and its consumer group if missing."""
        ...

    async def read(self, block_ms: int) -> Job | None:
        """Wait up to ``block_ms`` for a new entry."""
        ...

    async def reclaim(self, min_idle_ms: int) -> Job | None:
        """Take over one entry another consumer left idle for ``min_idle_ms``."""
        ...

    async def refresh(self, job: Job) -> None:
        """Reset the idle time of a job this consumer is still working on."""
        ...

    async def ack(self, job: Job) -> None:
        """Acknowledge and delete the entry (``XACK`` + ``XDEL``)."""
        ...

    async def dead_letter(self, letter: DeadLetter) -> None:
        """Append a record to ``docs:dead``."""
        ...
