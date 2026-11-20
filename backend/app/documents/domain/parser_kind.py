"""The three parsers a user can pick; their values are the API literals."""

from enum import StrEnum


class ParserKind(StrEnum):
    """A parser choice. ``pypdf`` returns text; the two models return markdown."""

    PYPDF = "pypdf"
    GEMINI = "gemini-3.1-flash-lite"
    GPT5_MINI = "gpt-5-mini"

    @property
    def uses_model(self) -> bool:
        """True when parsing spends model pages from the daily budget."""
        return self is not ParserKind.PYPDF

    @classmethod
    def allowed(cls) -> list[str]:
        """The literal values, in the order the page offers them."""
        return [kind.value for kind in cls]

    @classmethod
    def parse(cls, raw: str | None) -> "ParserKind | None":
        """Return the kind for an exact value, or None (no case folding, no trimming)."""
        try:
            return cls(raw) if raw is not None else None
        except ValueError:
            return None
