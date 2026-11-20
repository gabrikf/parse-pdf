"""Port: one chat completion through OpenRouter (door 7)."""

from dataclasses import dataclass, field
from typing import Any, Protocol


@dataclass(frozen=True, slots=True)
class ChatRequest:
    """A model id, the messages, and the optional OpenRouter extras."""

    model: str
    messages: list[dict[str, Any]]
    response_format: dict[str, Any] | None = None
    plugins: list[dict[str, Any]] = field(default_factory=list)
    max_tokens: int | None = None
    reasoning_effort: str | None = None
    timeout_s: float | None = None  # overrides the client deadline for this call


class ChatModel(Protocol):
    """Returns the assistant text; raises ``PermanentFailure`` / ``TransientFailure``."""

    async def complete(self, request: ChatRequest) -> str:
        """Send the request (rate limited and retried) and return the reply text."""
        ...
