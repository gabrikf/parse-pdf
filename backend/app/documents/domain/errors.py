"""Rule violations raised by use cases; the HTTP layer maps each code to a status."""


class DomainError(Exception):
    """A refused operation with a stable snake_case code."""

    code: str = "domain_error"
    message: str = "The operation is not allowed."

    def __init__(self, message: str | None = None) -> None:
        super().__init__(message or self.message)
        if message:
            self.message = message


class DocumentNotFoundError(DomainError):
    """The id does not exist, or belongs to another session (never told apart)."""

    code = "document_not_found"
    message = "No document with this id."


class DocumentBusyError(DomainError):
    """The document is queued or processing, so it cannot be changed now."""

    code = "document_busy"
    message = "The document is being processed."


class NotReparsableError(DomainError):
    """A ``too_large`` document can never be parsed."""

    code = "not_reparsable"
    message = "This document cannot be parsed."


class NotDeadError(DomainError):
    """Requeue applies only to dead documents."""

    code = "not_dead"
    message = "Only failed documents can be retried."


class NotReadyError(DomainError):
    """Pages are visible only when the document is ready (AD-004)."""

    code = "not_ready"
    message = "The document is not ready."


class ModelBudgetExhaustedError(DomainError):
    """The daily model page budget would be passed."""

    code = "model_budget_exhausted"
    message = "Today's model page budget would be exceeded."
