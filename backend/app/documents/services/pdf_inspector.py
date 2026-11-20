"""Open an uploaded PDF in a killable child process, with a 10 s deadline."""

from app.core.isolated import IsolatedCrashError, IsolatedRunner, IsolatedTimeoutError
from app.parsers.pdf_tools import Inspection, InspectionVerdict, inspect_pdf


class PdfInspector:
    """Counts pages and unlocks encrypted files without ever blocking the event loop.

    A file that crashes, exhausts the child's memory or runs past the deadline is reported
    ``unreadable_pdf``.
    """

    def __init__(self, runner: IsolatedRunner, timeout_s: float, max_pages: int) -> None:
        self._runner = runner
        self._timeout_s = timeout_s
        self._max_pages = max_pages

    async def inspect(self, data: bytes, password: str | None) -> Inspection:
        """Return the verdict for one file."""
        try:
            result: Inspection = await self._runner.run(
                inspect_pdf, (data, password, self._max_pages), self._timeout_s
            )
        except (IsolatedTimeoutError, IsolatedCrashError):
            return Inspection(InspectionVerdict.UNREADABLE)
        return result
