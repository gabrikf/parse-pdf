"""Envelope responses for controllers."""

from collections.abc import Mapping
from typing import Any

from fastapi.responses import JSONResponse

from app.core.envelope import success


def ok(data: Any, status: int = 200, meta: Mapping[str, Any] | None = None) -> JSONResponse:
    """A success envelope."""
    return JSONResponse(success(data, meta), status_code=status)
