"""Criterion 45: a rerun whose restart fails gives its reserved model pages back."""

from typing import Any

import pytest

from app.documents.domain.document_status import DocumentStatus
from app.documents.domain.parser_kind import ParserKind
from app.documents.use_cases.rerun_documents import BudgetedRestart
from tests.fakes import FakeBudget, FakeClock
from tests.integration.seed import draft


class FailingRepository:
    """``restart_run`` fails the way a dropped Redis connection does."""

    async def restart_run(self, *_: Any) -> None:
        raise ConnectionError("redis went away")


async def test_a_failed_restart_releases_the_reserved_pages() -> None:
    budget = FakeBudget(used=100)
    restart = BudgetedRestart(FailingRepository(), budget, FakeClock())  # type: ignore[arg-type]
    document = draft("s", status=DocumentStatus.DEAD, parser=ParserKind.GEMINI, page_count=10)

    with pytest.raises(ConnectionError):
        await restart(document, frozenset({DocumentStatus.DEAD}), ParserKind.GEMINI)

    assert budget.used == 100
