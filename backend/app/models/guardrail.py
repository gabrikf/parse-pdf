"""Port: a safety classifier run on summary input and output (AD-009)."""

from typing import Protocol


class Guardrail(Protocol):
    """Says whether a text is safe to summarize or to show."""

    async def is_safe(self, text: str) -> bool:
        """True when the classifier answers ``safe``."""
        ...
