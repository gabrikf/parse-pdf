"""Strict parsing of query parameters into the API's own 422 codes."""

from app.core.errors import AppError
from app.documents.domain.document_status import FeedState


def parse_bounded_int(raw: str | None, default: int, low: int, high: int, code: str) -> int:
    """Parse an integer in ``[low, high]``; anything else is ``422 <code>``."""
    if raw is None:
        return default
    # ASCII digits only and at most 9 of them: "²" passes isdigit() and int() refuses it, and a
    # very long string trips int()'s digit limit; both must be the 422, not a 500.
    if not (raw.isascii() and raw.isdigit() and len(raw) <= 9) or not low <= int(raw) <= high:
        message = f"Must be a whole number from {low} to {high}."
        raise AppError(422, code, message, {"min": low, "max": high})
    return int(raw)


def parse_state(raw: str | None) -> FeedState:
    """Parse ``state``; omitted means ``all``, anything unknown (``""`` too) is ``422``."""
    if raw is None:
        return FeedState.ALL
    try:
        return FeedState(raw)
    except ValueError:
        allowed = [state.value for state in FeedState]
        raise AppError(422, "invalid_state", "Unknown state.", {"allowed": allowed}) from None
