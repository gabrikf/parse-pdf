"""Admission for OpenRouter calls: 30 per rolling minute shared, 1 at a time per worker."""

import asyncio
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from app.models.retry_policy import Sleep
from app.rate_limit.rate_limiter import RateLimiter

OPENROUTER_WINDOW_KEY = "ratelimit:openrouter"
WINDOW_S = 60


class ModelCallGate:
    """A call over the shared limit waits for its slot instead of failing (AD-008)."""

    def __init__(
        self, limiter: RateLimiter, calls_per_minute: int, sleep: Sleep = asyncio.sleep
    ) -> None:
        self._limiter = limiter
        self._limit = calls_per_minute
        self._sleep = sleep
        self._local = asyncio.Semaphore(1)

    @asynccontextmanager
    async def slot(self) -> AsyncIterator[None]:
        """Hold the worker's single slot and one hit of the shared window."""
        async with self._local:
            while True:
                decision = await self._limiter.hit(OPENROUTER_WINDOW_KEY, self._limit, WINDOW_S)
                if decision.allowed:
                    break
                await self._sleep(decision.retry_after_s)
            yield
