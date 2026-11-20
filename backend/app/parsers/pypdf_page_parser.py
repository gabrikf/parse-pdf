"""``PageParser`` with pypdf: plain text per page, extracted in a killable child process."""

from app.core.isolated import IsolatedCrashError, IsolatedRunner, IsolatedTimeoutError
from app.documents.domain.job_errors import PermanentFailure
from app.documents.domain.page import Page, PageFormat
from app.parsers.page_parser import ParseRequest
from app.parsers.pdf_tools import extract_text_pages


class PypdfPageParser:
    """A parse past its deadline (300 s) ends ``parse_timeout``; a crash ``unreadable_pdf``."""

    def __init__(self, runner: IsolatedRunner, timeout_s: float) -> None:
        self._runner = runner
        self._timeout_s = timeout_s

    async def parse(self, request: ParseRequest) -> list[Page]:
        """Return one text page per PDF page."""
        try:
            texts: list[str] = await self._runner.run(
                extract_text_pages, (request.pdf,), self._timeout_s
            )
        except IsolatedTimeoutError as exc:
            raise PermanentFailure("parse_timeout") from exc
        except IsolatedCrashError as exc:
            raise PermanentFailure("unreadable_pdf") from exc
        return [Page(number, text, PageFormat.TEXT) for number, text in enumerate(texts, 1)]
