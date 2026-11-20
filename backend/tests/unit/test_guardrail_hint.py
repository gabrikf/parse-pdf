"""Criterion 31: a guardrail rejection tells the person what was flagged and where (AD-056)."""

import pytest

from app.documents.services.guardrail_hint import GuardedText, guardrail_hint


def test_hint_names_one_category_and_the_document_text() -> None:
    hint = guardrail_hint(frozenset({"S1"}), GuardedText.DOCUMENT)

    assert hint == (
        "The safety check flagged the document's text for violent crimes (S1), so no summary "
        "was written. A retry with the same text will most likely be flagged again."
    )


def test_hint_names_the_summary_when_the_output_was_flagged() -> None:
    hint = guardrail_hint(frozenset({"S12"}), GuardedText.SUMMARY)

    assert hint.startswith("The safety check flagged the written summary for sexual content (S12)")


def test_hint_lists_several_categories_in_number_order() -> None:
    hint = guardrail_hint(frozenset({"S10", "S2", "S6"}), GuardedText.DOCUMENT)

    assert (
        "for non-violent crimes (S2), specialized advice (S6) and hate (S10), so no summary" in hint
    )


@pytest.mark.parametrize(
    ("categories", "expected"),
    [
        (frozenset(), "for unsafe content (no category given), so"),
        (frozenset({"S60"}), "for an unlisted category (S60), so"),
    ],
)
def test_hint_without_a_known_category_still_reads(
    categories: frozenset[str], expected: str
) -> None:
    assert expected in guardrail_hint(categories, GuardedText.DOCUMENT)
