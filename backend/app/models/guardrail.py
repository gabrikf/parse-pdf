"""Port: a safety classifier run on summary input and output (AD-009)."""

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True, slots=True)
class GuardVerdict:
    """Whether the text may pass, and the hazard categories the classifier named (``S1``..)."""

    safe: bool
    categories: frozenset[str] = frozenset()


class Guardrail(Protocol):
    """Judges whether a text is safe to summarize or to show."""

    async def check(self, text: str) -> GuardVerdict:
        """The verdict; ``categories`` says what was flagged, so the person can be told."""
        ...
