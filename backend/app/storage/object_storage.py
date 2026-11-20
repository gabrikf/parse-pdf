"""Port: PDF bytes in an S3-compatible bucket (door 5)."""

from typing import Protocol


def object_key_for(document_id: str) -> str:
    """The key of a document's PDF; never derived from the uploaded filename."""
    return f"documents/{document_id}.pdf"


class ObjectStorage(Protocol):
    """Put, get and delete whole objects."""

    async def put(self, key: str, data: bytes) -> None:
        """Store ``data`` at ``key``."""
        ...

    async def get(self, key: str) -> bytes:
        """Return the bytes at ``key``."""
        ...

    async def delete(self, key: str) -> None:
        """Remove ``key``; a missing key is not an error."""
        ...

    async def is_ready(self) -> bool:
        """True when the bucket exists and answers."""
        ...
