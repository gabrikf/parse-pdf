"""How a job step failed, which decides whether the worker retries or gives up."""


class PermanentFailure(Exception):  # noqa: N818 - a failure outcome, not a bug report
    """Retrying cannot help: the document ends ``dead`` with ``code``.

    ``hint`` is the sentence the person reads on the failed card when the code alone cannot say
    what went wrong (which pages, which safety category); without one the page words the code.
    """

    def __init__(self, code: str, detail: str = "", *, hint: str | None = None) -> None:
        super().__init__(detail or code)
        self.code = code
        self.hint = hint


class TransientFailure(Exception):  # noqa: N818 - a failure outcome, not a bug report
    """Retries inside this delivery ran out; the entry stays pending for redelivery."""
