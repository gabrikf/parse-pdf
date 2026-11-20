"""Pick the parser for a document's parser kind."""

from collections.abc import Mapping

from app.documents.domain.parser_kind import ParserKind
from app.parsers.page_parser import PageParser


class ParserSelector:
    """Maps each of the three kinds to its parser; built once in the container."""

    def __init__(self, parsers: Mapping[ParserKind, PageParser]) -> None:
        missing = set(ParserKind) - set(parsers)
        if missing:
            raise ValueError(f"no parser for {sorted(missing)}")
        self._parsers = dict(parsers)

    def pick(self, kind: ParserKind) -> PageParser:
        """Return the parser for ``kind``."""
        return self._parsers[kind]
