"""Door 8: the in-flight counter frees its slot in one step and never goes below zero."""

from redis.asyncio import Redis

from app.rate_limit.redis_sliding_window import RedisInFlightCounter


async def test_release_frees_the_last_slot_and_never_leaves_a_negative_count(
    redis: Redis,
) -> None:
    counter = RedisInFlightCounter(redis)
    key = "inflight:upload:test-session"

    assert await counter.acquire(key, 2)
    assert await counter.acquire(key, 2)
    assert not await counter.acquire(key, 2)

    await counter.release(key)
    assert await redis.get(key) == "1"
    await counter.release(key)
    assert await redis.exists(key) == 0

    await counter.release(key)  # a slot whose key already expired
    assert await redis.exists(key) == 0
    assert await counter.acquire(key, 2)
    assert await counter.acquire(key, 2)
    assert not await counter.acquire(key, 2)
