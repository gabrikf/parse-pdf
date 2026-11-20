"""Time behind an interface, so limits, TTLs and the budget's UTC day are testable."""

from datetime import UTC, datetime
from typing import Protocol


class Clock(Protocol):
    """Source of the current time."""

    def now(self) -> datetime:
        """Return the current UTC time."""
        ...


class SystemClock:
    """The wall clock, in UTC."""

    def now(self) -> datetime:
        """Return the current UTC time."""
        return datetime.now(UTC)


def to_millis(moment: datetime) -> int:
    """Express a moment as Unix milliseconds (the feed index score)."""
    return int(moment.timestamp() * 1000)


def to_iso(moment: datetime) -> str:
    """Express a moment as an ISO-8601 UTC string with a ``Z`` suffix."""
    return moment.astimezone(UTC).isoformat(timespec="milliseconds").replace("+00:00", "Z")
