"""Key names of door 1, written once."""

from app.documents.domain.document_status import FeedState

DOCUMENT_TTL_S = 604_800


def doc_key(document_id: str) -> str:
    """The record hash."""
    return f"doc:{document_id}"


def pages_key(document_id: str) -> str:
    """The list of page JSON objects."""
    return f"doc:{document_id}:pages"


def chunks_key(document_id: str) -> str:
    """The model-chunk checkpoints: ``chunk_index -> pages JSON``."""
    return f"doc:{document_id}:chunks"


def feed_key(session_id: str, state: FeedState = FeedState.ALL) -> str:
    """A session's feed index, all documents or one group, scored by ``created_at`` ms."""
    base = f"session:{session_id}:docs"
    return base if state is FeedState.ALL else f"{base}:{state.value}"
