"""Port: the global daily budget of model pages (AD-013)."""

from dataclasses import dataclass
from datetime import datetime
from typing import Protocol


@dataclass(frozen=True, slots=True)
class BudgetUsage:
    """Today's count, the cap, and when the UTC day ends."""

    used: int
    limit: int
    resets_at: datetime


class ModelBudget(Protocol):
    """Model pages counted per UTC day across every process."""

    async def reserve(self, pages: int) -> bool:
        """Count ``pages`` if the total stays within the cap; False otherwise."""
        ...

    async def release(self, pages: int) -> None:
        """Give back pages reserved for a file that was not stored."""
        ...

    async def add(self, pages: int) -> None:
        """Count pages that are always allowed (one per summary)."""
        ...

    async def usage(self) -> BudgetUsage:
        """Return today's usage."""
        ...
