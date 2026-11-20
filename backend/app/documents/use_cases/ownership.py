"""Load a document only for its owner; anyone else gets the same answer as a missing id."""

from app.documents.domain.document import Document
from app.documents.domain.errors import DocumentNotFoundError
from app.repositories.document_repository import DocumentRepository


async def load_owned(repository: DocumentRepository, document_id: str, session_id: str) -> Document:
    """Return the document, or raise ``DocumentNotFoundError`` (never a 403, ids do not leak)."""
    document = await repository.get(document_id)
    if document is None or document.session_id != session_id:
        raise DocumentNotFoundError
    return document
