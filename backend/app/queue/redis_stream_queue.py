"""``JobQueue`` on Redis Streams: one consumer group, explicit acks, reclaim by idle time."""

from typing import Any

from redis.asyncio import Redis
from redis.exceptions import ResponseError

from app.queue.job import CONSUMER_GROUP, DEAD_LETTER_KEY, STREAM_KEY, DeadLetter, Job


def _job(entry_id: str, fields: dict[str, str]) -> Job:
    return Job(
        entry_id=entry_id,
        document_id=fields.get("document_id", ""),
        object_key=fields.get("object_key", ""),
        run_id=fields.get("run_id", ""),
    )


class RedisStreamQueue:
    """The consumer ``{hostname}-{pid}`` of group ``parsers`` on ``docs:stream`` (door 2)."""

    def __init__(self, redis: Redis, consumer: str) -> None:
        self._redis = redis
        self._consumer = consumer
        self._reclaim_cursor = "0-0"

    async def ensure_group(self) -> None:
        """Create the group at the start of the stream; an existing group is kept."""
        try:
            await self._redis.xgroup_create(STREAM_KEY, CONSUMER_GROUP, id="0", mkstream=True)
        except ResponseError as exc:
            if "BUSYGROUP" not in str(exc):
                raise

    async def read(self, block_ms: int) -> Job | None:
        """``XREADGROUP ... >``: one new entry, or None after ``block_ms``."""
        reply: Any = await self._redis.xreadgroup(
            CONSUMER_GROUP, self._consumer, {STREAM_KEY: ">"}, count=1, block=block_ms
        )
        if not reply:
            return None
        _, entries = reply[0]
        entry_id, fields = entries[0]
        return _job(entry_id, fields)

    async def reclaim(self, min_idle_ms: int) -> Job | None:
        """``XAUTOCLAIM`` one entry idle for at least ``min_idle_ms``."""
        reply: Any = await self._redis.xautoclaim(
            STREAM_KEY,
            CONSUMER_GROUP,
            self._consumer,
            min_idle_time=min_idle_ms,
            start_id=self._reclaim_cursor,
            count=1,
        )
        next_cursor, entries = reply[0], reply[1]
        self._reclaim_cursor = next_cursor
        for entry_id, fields in entries:
            if fields:
                return _job(entry_id, fields)
        return None

    async def refresh(self, job: Job) -> None:
        """``XCLAIM ... JUSTID`` to our own consumer: resets the idle time, keeps the count."""
        await self._redis.xclaim(
            STREAM_KEY, CONSUMER_GROUP, self._consumer, 0, [job.entry_id], justid=True
        )

    async def ack(self, job: Job) -> None:
        """Acknowledge and delete; the stream is never trimmed by length (AD-016)."""
        async with self._redis.pipeline(transaction=True) as pipe:
            pipe.xack(STREAM_KEY, CONSUMER_GROUP, job.entry_id)
            pipe.xdel(STREAM_KEY, job.entry_id)
            await pipe.execute()

    async def dead_letter(self, letter: DeadLetter) -> None:
        """Keep a record of a job that gave up."""
        await self._redis.xadd(
            DEAD_LETTER_KEY,
            {
                "document_id": letter.document_id,
                "run_id": letter.run_id,
                "error_code": letter.error_code,
                "deliveries": str(letter.deliveries),
            },
        )
