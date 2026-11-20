"""Plain words for why a delivery failed, and the message a document gets when its tries run out."""

import re

UNKNOWN_CAUSE = "the worker stopped before it finished"
UNEXPECTED_CAUSE = "an unexpected error in the worker"
_STATUS = re.compile(r"^status (\d{3})$")
_CAUSES = {
    "timeout": "the model provider timed out",
    "transport error": "the model provider could not be reached",
    "guardrail verdict unreadable": "the safety check's answer could not be read",
}


def describe_cause(reason: str) -> str:
    """Turn a retry reason (``timeout``, ``status 502``) into a short cause a person can read."""
    if reason in _CAUSES:
        return _CAUSES[reason]
    status = _STATUS.match(reason)
    if status is None:
        return "the model provider's answer could not be used"
    if status.group(1) == "429":
        return "the model provider kept refusing calls (status 429)"
    return f"the model provider answered with status {status.group(1)}"


def exhausted_hint_prefix(tries: int) -> str:
    """The start of the ``max_deliveries`` hint; the last recorded cause and a full stop follow."""
    return f"Processing stopped after {tries} tries. The last error was: "
