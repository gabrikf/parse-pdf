"""Exponential backoff with full jitter for transient OpenRouter failures."""

import asyncio
import random
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field

from app.documents.domain.job_errors import TransientFailure


class RetryableError(Exception):
    """A 429, a 5xx or a timeout; ``retry_after_s`` comes from the ``Retry-After`` header."""

    def __init__(self, reason: str, retry_after_s: float | None = None) -> None:
        super().__init__(reason)
        self.retry_after_s = retry_after_s


Sleep = Callable[[float], Awaitable[None]]


@dataclass
class RetryPolicy:
    """6 attempts, 1 s base doubling to a 60 s cap, full jitter, never sooner than Retry-After.

    When every attempt fails the policy raises ``TransientFailure``: the worker then leaves the
    job pending for redelivery instead of setting it ``dead``.
    """

    attempts: int = 6
    base_s: float = 1.0
    cap_s: float = 60.0
    sleep: Sleep = asyncio.sleep
    jitter: Callable[[float, float], float] = field(default=random.uniform)

    def delay(self, attempt: int, retry_after_s: float | None) -> float:
        """Seconds to wait after the 0-based ``attempt`` failed."""
        backoff = self.jitter(0, min(self.cap_s, self.base_s * 2**attempt))
        return max(backoff, retry_after_s or 0.0)

    async def run[T](self, call: Callable[[], Awaitable[T]]) -> T:
        """Run ``call`` until it succeeds or the attempts run out."""
        for attempt in range(self.attempts):
            try:
                return await call()
            except RetryableError as exc:
                if attempt == self.attempts - 1:
                    raise TransientFailure(str(exc)) from exc
                await self.sleep(self.delay(attempt, exc.retry_after_s))
        raise TransientFailure("no attempt was made")
