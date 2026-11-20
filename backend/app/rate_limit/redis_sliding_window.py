"""``RateLimiter`` and ``InFlightCounter`` on Redis, so limits hold across every process."""

import math
from importlib import resources

from redis.asyncio import Redis

from app.core.clock import Clock, to_millis
from app.core.ids import new_id
from app.rate_limit.rate_limiter import RateDecision

IN_FLIGHT_TTL_S = 120


def _script(name: str) -> str:
    return resources.files("app.rate_limit").joinpath(f"lua/{name}.lua").read_text()


class RedisSlidingWindow:
    """A sorted set of hit times per key; a hit over the limit is refused, not counted."""

    def __init__(self, redis: Redis, clock: Clock) -> None:
        self._clock = clock
        self._script = redis.register_script(_script("sliding_window"))

    async def hit(self, key: str, limit: int, window_s: int) -> RateDecision:
        """Count one hit if it fits; otherwise say how many whole seconds to wait."""
        now_ms = to_millis(self._clock.now())
        allowed, retry_ms = await self._script(
            keys=[key], args=[now_ms, window_s * 1000, limit, f"{now_ms}-{new_id()}"]
        )
        if int(allowed) == 1:
            return RateDecision(allowed=True)
        return RateDecision(allowed=False, retry_after_s=max(1, math.ceil(int(retry_ms) / 1000)))


class RedisInFlightCounter:
    """``INCR`` with a safety TTL, so a crashed request frees its slot after 120 s."""

    def __init__(self, redis: Redis) -> None:
        self._redis = redis
        self._script = redis.register_script(_script("in_flight"))

    async def acquire(self, key: str, maximum: int) -> bool:
        """Take a slot when fewer than ``maximum`` are taken."""
        return int(await self._script(keys=[key], args=[maximum, IN_FLIGHT_TTL_S])) == 1

    async def release(self, key: str) -> None:
        """Give the slot back; the counter never goes below zero."""
        if int(await self._redis.decr(key)) <= 0:
            await self._redis.delete(key)
