"""The response envelope ``{data, error, meta}`` shared by every JSON body (door 3)."""

from collections.abc import Mapping
from typing import Any

from app.core.request_context import current_request_id


def _meta(extra: Mapping[str, Any] | None) -> dict[str, Any]:
    meta: dict[str, Any] = {"request_id": current_request_id()}
    meta.update(extra or {})
    return meta


def success(data: Any, meta: Mapping[str, Any] | None = None) -> dict[str, Any]:
    """Wrap a successful result."""
    return {"data": data, "error": None, "meta": _meta(meta)}


def failure(code: str, message: str, details: Mapping[str, Any] | None = None) -> dict[str, Any]:
    """Wrap an error; ``details`` is always an object so clients never branch on its type."""
    error = {"code": code, "message": message, "details": dict(details or {})}
    return {"data": None, "error": error, "meta": _meta(None)}
