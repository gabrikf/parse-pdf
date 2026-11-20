"""Delete a document for good: record, pages, chunks, feed entries and its PDF."""

from app.documents.domain.errors import DocumentBusyError
from app.documents.domain.transitions import ensure_deletable
from app.documents.use_cases.ownership import load_owned
from app.repositories.document_repository import DocumentRepository
from app.storage.object_storage import ObjectStorage


class DeleteDocumentUseCase:
    """Refused while ``processing``; a ``queued`` entry left in the stream is dropped as stale."""

    def __init__(self, repository: DocumentRepository, storage: ObjectStorage) -> None:
        self._repository = repository
        self._storage = storage

    async def execute(self, session_id: str, document_id: str) -> str:
        """Return the id of the deleted document."""
        document = await load_owned(self._repository, document_id, session_id)
        ensure_deletable(document.status)

        if not await self._repository.delete(document):
            raise DocumentBusyError
        if document.object_key:
            await self._storage.delete(document.object_key)
        return document.id
