"""Per-request values that logs and envelopes read without passing them around."""

from contextvars import ContextVar

request_id_var: ContextVar[str] = ContextVar("request_id", default="-")


def current_request_id() -> str:
    """Return the id of the request being served, or ``-`` outside a request."""
    return request_id_var.get()
