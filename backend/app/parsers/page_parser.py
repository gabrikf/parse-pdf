"""Port: turn a PDF into one string per page (door 7)."""

from dataclasses import dataclass
from typing import Protocol

from app.documents.domain.document import Document
from app.documents.domain.page import Page


class ChunkCheckpoint(Protocol):
    """Where a model parser saves finished chunks, so a reclaimed job resumes."""

    async def load(self) -> dict[int, list[Page]]:
        """Return the chunks saved for the current run."""
        ...

    async def save(self, index: int, pages: list[Page]) -> None:
        """Save one finished chunk."""
        ...


@dataclass(frozen=True, slots=True)
class ParseRequest:
    """Everything a parser needs for one run."""

    document: Document
    pdf: bytes
    checkpoint: ChunkCheckpoint


class PageParser(Protocol):
    """A parser; raises ``PermanentFailure`` or ``TransientFailure`` on error."""

    async def parse(self, request: ParseRequest) -> list[Page]:
        """Return the pages in order, numbered from 1."""
        ...
