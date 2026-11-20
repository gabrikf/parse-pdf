"""How a job step failed, which decides whether the worker retries or gives up."""


class PermanentFailure(Exception):  # noqa: N818 - a failure outcome, not a bug report
    """Retrying cannot help: the document ends ``dead`` with ``code``."""

    def __init__(self, code: str, detail: str = "") -> None:
        super().__init__(detail or code)
        self.code = code


class TransientFailure(Exception):  # noqa: N818 - a failure outcome, not a bug report
    """Retries inside this delivery ran out; the entry stays pending for redelivery."""
