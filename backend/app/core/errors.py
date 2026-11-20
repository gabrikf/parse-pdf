"""The one error type the HTTP layer turns into an envelope."""

from collections.abc import Mapping
from typing import Any


class AppError(Exception):
    """An expected failure with a stable snake_case ``code`` and the HTTP status that carries it.

    Raised by controllers and middleware; the exception handler in ``app.main`` renders it as
    ``{"data": null, "error": {code, message, details}, "meta": {...}}``.
    """

    def __init__(
        self,
        status: int,
        code: str,
        message: str,
        details: Mapping[str, Any] | None = None,
        headers: Mapping[str, str] | None = None,
    ) -> None:
        super().__init__(message)
        self.status = status
        self.code = code
        self.message = message
        self.details = dict(details or {})
        self.headers = dict(headers or {})
