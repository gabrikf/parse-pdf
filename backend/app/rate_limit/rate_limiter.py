"""Port: limits shared by every API process and worker (door 8)."""

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True, slots=True)
class RateDecision:
    """Whether a hit fits the window, and how long to wait when it does not."""

    allowed: bool
    retry_after_s: int = 0


class RateLimiter(Protocol):
    """A sliding-window counter."""

    async def hit(self, key: str, limit: int, window_s: int) -> RateDecision:
        """Record one hit on ``key`` if it fits ``limit`` per ``window_s``."""
        ...


class InFlightCounter(Protocol):
    """A counter of requests running right now."""

    async def acquire(self, key: str, maximum: int) -> bool:
        """Take a slot; False when ``maximum`` are already taken."""
        ...

    async def release(self, key: str) -> None:
        """Give a slot back."""
        ...
