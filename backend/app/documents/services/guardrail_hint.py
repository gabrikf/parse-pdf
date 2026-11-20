"""The failed card's sentence when the safety check blocks a document (AD-056).

Llama Guard 4 names hazards as S1..S14; the person reads their names, not the codes alone.
"""

from enum import StrEnum

CATEGORY_NAMES = {
    "S1": "violent crimes",
    "S2": "non-violent crimes",
    "S3": "sex-related crimes",
    "S4": "child sexual exploitation",
    "S5": "defamation",
    "S6": "specialized advice",
    "S7": "privacy",
    "S8": "intellectual property",
    "S9": "indiscriminate weapons",
    "S10": "hate",
    "S11": "suicide and self-harm",
    "S12": "sexual content",
    "S13": "elections",
    "S14": "code interpreter abuse",
}


class GuardedText(StrEnum):
    """Which text the safety check was reading when it said no."""

    DOCUMENT = "document's text"
    SUMMARY = "written summary"


def guardrail_hint(categories: frozenset[str], where: GuardedText) -> str:
    """Say what was flagged and where, and that the same text will most likely be flagged again."""
    flagged = _named(categories)
    return (
        f"The safety check flagged the {where.value} for {flagged}, so no summary was "
        "written. A retry with the same text will most likely be flagged again."
    )


def _named(categories: frozenset[str]) -> str:
    if not categories:
        return "unsafe content (no category given)"

    ordered = sorted(categories, key=lambda code: int(code[1:]))
    names = [f"{CATEGORY_NAMES.get(code, 'an unlisted category')} ({code})" for code in ordered]
    if len(names) == 1:
        return names[0]
    return f"{', '.join(names[:-1])} and {names[-1]}"
