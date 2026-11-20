"""Small in-memory stand-ins for ports, used where a real dependency adds nothing."""

from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta

from app.models.chat_model import ChatRequest
from app.rate_limit.model_budget import BudgetUsage

GUARD_MODEL = "meta-llama/llama-guard-4-12b"


@dataclass
class FakeChat:
    """Answers guard calls with ``guard_verdict`` and every other call with ``reply``."""

    reply: str = "## Overview\nA short summary.\n\n## Key points\n- one"
    guard_verdict: str = "safe"
    calls: list[ChatRequest] = field(default_factory=list)

    async def complete(self, request: ChatRequest) -> str:
        self.calls.append(request)
        return self.guard_verdict if request.model == GUARD_MODEL else self.reply

    def calls_to(self, model: str) -> list[ChatRequest]:
        return [call for call in self.calls if call.model == model]


@dataclass
class FakeBudget:
    """A budget counter in memory."""

    used: int = 0
    limit: int = 3000

    async def reserve(self, pages: int) -> bool:
        if self.used + pages > self.limit:
            return False
        self.used += pages
        return True

    async def release(self, pages: int) -> None:
        self.used -= pages

    async def add(self, pages: int) -> None:
        self.used += pages

    async def usage(self) -> BudgetUsage:
        tomorrow = datetime(2026, 11, 20, tzinfo=UTC)
        return BudgetUsage(self.used, self.limit, tomorrow)


@dataclass
class FakeClock:
    """A clock tests move by hand."""

    current: datetime = datetime(2026, 11, 19, 12, 0, tzinfo=UTC)

    def now(self) -> datetime:
        return self.current

    def advance(self, seconds: float) -> None:
        self.current += timedelta(seconds=seconds)
