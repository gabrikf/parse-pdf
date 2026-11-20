"""The queue contract (door 2): stream names and the entry a worker receives."""

from dataclasses import dataclass

STREAM_KEY = "docs:stream"
DEAD_LETTER_KEY = "docs:dead"
CONSUMER_GROUP = "parsers"


@dataclass(frozen=True, slots=True)
class Job:
    """A stream entry: only ids, never document content."""

    entry_id: str
    document_id: str
    object_key: str
    run_id: str


@dataclass(frozen=True, slots=True)
class DeadLetter:
    """What ``docs:dead`` keeps about a job that gave up."""

    document_id: str
    run_id: str
    error_code: str
    deliveries: int
