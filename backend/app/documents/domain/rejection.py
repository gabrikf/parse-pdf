"""Why a file of an upload was refused, and the copy the page shows for it."""

from dataclasses import dataclass
from enum import StrEnum


class RejectionCode(StrEnum):
    """Per-file refusal codes listed in ``data.rejected[]``."""

    EMPTY = "empty"
    NOT_PDF = "not_pdf"
    UNREADABLE_PDF = "unreadable_pdf"
    LOCKED = "password_required"
    UNLOCK_FAILED = "wrong_password"
    MODEL_BUDGET_EXHAUSTED = "model_budget_exhausted"


REJECTION_MESSAGES: dict[RejectionCode, str] = {
    RejectionCode.EMPTY: "The file is empty.",
    RejectionCode.NOT_PDF: "The file is not a PDF.",
    RejectionCode.UNREADABLE_PDF: "The PDF could not be opened.",
    RejectionCode.LOCKED: "The PDF needs a password.",
    RejectionCode.UNLOCK_FAILED: "The password does not open this PDF.",
    RejectionCode.MODEL_BUDGET_EXHAUSTED: "Today's model page budget would be exceeded.",
}


@dataclass(frozen=True, slots=True)
class Rejection:
    """A refused file: its display name and the reason code."""

    filename: str
    code: RejectionCode

    @property
    def message(self) -> str:
        """The sentence the page shows next to the file."""
        return REJECTION_MESSAGES[self.code]
