"""One parsed page."""

from dataclasses import dataclass
from enum import StrEnum


class PageFormat(StrEnum):
    """How a page's content is written: pypdf gives text, the models give markdown."""

    TEXT = "text"
    MARKDOWN = "markdown"


@dataclass(frozen=True, slots=True)
class Page:
    """The content of page ``number`` (1-based) of a document."""

    number: int
    content: str
    format: PageFormat

    @property
    def is_blank(self) -> bool:
        """True when the page holds no non-whitespace character."""
        return not self.content.strip()
