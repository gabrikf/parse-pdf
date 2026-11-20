"""Criterion 34: 30 OpenRouter calls per rolling minute across workers, 1 at a time per worker."""

import asyncio

from redis.asyncio import Redis

from app.models.call_gate import ModelCallGate
from app.rate_limit.redis_sliding_window import RedisSlidingWindow
from tests.fakes import FakeClock


async def test_40_calls_from_two_workers_start_30_then_10_after_60s(redis: Redis) -> None:
    clock = FakeClock()
    start = clock.now()
    started_at: list[float] = []

    async def sleep(seconds: float) -> None:
        clock.advance(seconds)
        await asyncio.sleep(0)

    workers = [ModelCallGate(RedisSlidingWindow(redis, clock), 30, sleep=sleep) for _ in range(2)]

    async def call(gate: ModelCallGate) -> None:
        async with gate.slot():
            started_at.append((clock.now() - start).total_seconds())

    await asyncio.gather(*(call(workers[i % 2]) for i in range(40)))

    assert len(started_at) == 40
    assert sum(1 for t in started_at if t < 60) == 30
    assert sum(1 for t in started_at if t >= 60) == 10


async def test_one_call_at_a_time_per_worker(redis: Redis) -> None:
    gate = ModelCallGate(RedisSlidingWindow(redis, FakeClock()), 30)
    running = 0
    peak = 0

    async def call() -> None:
        nonlocal running, peak
        async with gate.slot():
            running += 1
            peak = max(peak, running)
            await asyncio.sleep(0.01)
            running -= 1

    await asyncio.gather(*(call() for _ in range(5)))

    assert peak == 1
