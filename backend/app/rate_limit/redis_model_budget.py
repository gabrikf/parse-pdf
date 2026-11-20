"""``ModelBudget`` on a Redis counter per UTC day (door 8)."""

from datetime import datetime, time, timedelta
from importlib import resources

from redis.asyncio import Redis

from app.core.clock import Clock
from app.rate_limit.model_budget import BudgetUsage

DAY_KEY_TTL_S = 172_800


class RedisModelBudget:
    """``budget:model_pages:{YYYY-MM-DD}``, capped at ``MODEL_PAGE_BUDGET_PER_DAY``."""

    def __init__(self, redis: Redis, clock: Clock, limit: int) -> None:
        self._redis = redis
        self._clock = clock
        self._limit = limit
        source = resources.files("app.rate_limit").joinpath("lua/budget_reserve.lua")
        self._reserve = redis.register_script(source.read_text())

    def _key(self) -> str:
        return f"budget:model_pages:{self._clock.now().date().isoformat()}"

    async def reserve(self, pages: int) -> bool:
        """Count ``pages`` if today's total stays within the cap."""
        args = [pages, self._limit, DAY_KEY_TTL_S]
        return int(await self._reserve(keys=[self._key()], args=args)) == 1

    async def release(self, pages: int) -> None:
        """Give back pages of a file that was not stored."""
        await self._redis.decrby(self._key(), pages)

    async def add(self, pages: int) -> None:
        """Count pages that are never refused (one per summary)."""
        key = self._key()
        async with self._redis.pipeline(transaction=True) as pipe:
            pipe.incrby(key, pages)
            pipe.expire(key, DAY_KEY_TTL_S)
            await pipe.execute()

    async def usage(self) -> BudgetUsage:
        """Return today's count, the cap and the next UTC midnight."""
        now = self._clock.now()
        used = int(await self._redis.get(self._key()) or 0)
        resets_at = datetime.combine(now.date() + timedelta(days=1), time(), tzinfo=now.tzinfo)
        return BudgetUsage(used=used, limit=self._limit, resets_at=resets_at)
