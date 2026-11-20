"""The causes a person reads in the ``max_deliveries`` hint."""

import pytest

from app.documents.domain.failure_cause import describe_cause, exhausted_hint_prefix


@pytest.mark.parametrize(
    ("reason", "cause"),
    [
        ("timeout", "the model provider timed out"),
        ("transport error", "the model provider could not be reached"),
        ("status 429", "the model provider kept refusing calls (status 429)"),
        ("status 502", "the model provider answered with status 502"),
        ("guardrail verdict unreadable", "the safety check's answer could not be read"),
        ("invalid JSON", "the model provider's answer could not be used"),
    ],
)
def test_each_reason_reads_as_a_cause(reason: str, cause: str) -> None:
    assert describe_cause(reason) == cause


def test_the_hint_counts_the_tries() -> None:
    assert exhausted_hint_prefix(5) == "Processing stopped after 5 tries. The last error was: "
