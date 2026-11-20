"""Random identifiers: documents, runs and sessions are uuid4, never derived from input."""

import uuid


def new_id() -> str:
    """Return a new random uuid4 as a 36-character string."""
    return str(uuid.uuid4())
