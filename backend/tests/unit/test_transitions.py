"""Criteria 47-50 at the domain: which action each of the 6 statuses allows."""

import pytest

from app.documents.domain.document_status import DocumentStatus as S
from app.documents.domain.errors import DocumentBusyError, NotDeadError, NotReparsableError
from app.documents.domain.transitions import (
    ensure_deletable,
    ensure_reparsable,
    ensure_requeueable,
)

TABLE = [
    (S.QUEUED, DocumentBusyError, DocumentBusyError, None),
    (S.PROCESSING, DocumentBusyError, DocumentBusyError, DocumentBusyError),
    (S.READY, None, NotDeadError, None),
    (S.NO_TEXT, None, NotDeadError, None),
    (S.DEAD, None, None, None),
    (S.TOO_LARGE, NotReparsableError, NotDeadError, None),
]


def test_the_table_covers_every_status() -> None:
    assert {row[0] for row in TABLE} == set(S)


@pytest.mark.parametrize(("status", "reparse", "requeue", "delete"), TABLE)
def test_each_status_allows_or_refuses_each_action(
    status: S,
    reparse: type[Exception] | None,
    requeue: type[Exception] | None,
    delete: type[Exception] | None,
) -> None:
    for guard, expected in [
        (ensure_reparsable, reparse),
        (ensure_requeueable, requeue),
        (ensure_deletable, delete),
    ]:
        if expected is None:
            guard(status)
        else:
            with pytest.raises(expected):
                guard(status)
