"""An opaque feed cursor: the score and member of the last document a page returned.

Scores are ``created_at`` milliseconds, so files of one upload can tie; the member breaks the
tie the same way Redis orders a reversed range (member descending).
"""

import base64
import binascii
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class FeedCursor:
    """Position after which the next page starts."""

    score: int
    member: str

    def encode(self) -> str:
        """Return the URL-safe token clients send back."""
        raw = f"{self.score}:{self.member}".encode()
        return base64.urlsafe_b64encode(raw).decode().rstrip("=")

    @classmethod
    def decode(cls, token: str) -> "FeedCursor":
        """Parse a token; raises ``ValueError`` when it is not one of ours."""
        try:
            padded = token + "=" * (-len(token) % 4)
            score, member = base64.urlsafe_b64decode(padded).decode().split(":", 1)
            return cls(score=int(score), member=member)
        except (binascii.Error, UnicodeDecodeError, ValueError) as exc:
            raise ValueError("invalid cursor") from exc

    def is_after(self, score: int, member: str) -> bool:
        """True when (score, member) comes after this cursor in newest-first order."""
        return score < self.score or (score == self.score and member < self.member)
