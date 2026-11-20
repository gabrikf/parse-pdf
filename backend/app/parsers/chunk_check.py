"""What was wrong with a model's answer for one chunk, worded for the model and for a person.

The model reads the correction on its next try (AD-056); the person reads the hint on the
failed card once the tries run out. Page numbers are chunk-local (1..count) for the model, which
only sees the chunk, and document page numbers for the person.
"""

from dataclasses import dataclass
from enum import StrEnum


class AnswerProblem(StrEnum):
    """Why a chunk answer could not be used."""

    NONE = "none"
    NOT_JSON = "not_json"
    WRONG_SHAPE = "wrong_shape"
    WRONG_PAGES = "wrong_pages"


@dataclass(frozen=True, slots=True)
class ChunkCheck:
    """The page texts when the answer is valid, otherwise the problem and the faulty pages."""

    texts: list[str] | None = None
    problem: AnswerProblem = AnswerProblem.NONE
    missing: tuple[int, ...] = ()
    repeated: tuple[int, ...] = ()
    extra: tuple[int, ...] = ()


def correction(check: ChunkCheck, count: int) -> str:
    """The message sent back to the model so its next answer fixes exactly this problem."""
    if check.problem is AnswerProblem.NOT_JSON:
        return (
            "Your previous answer was not valid JSON; it may have been cut off. Answer again "
            "with only the JSON object, every page complete, and no text outside it."
        )
    if check.problem is AnswerProblem.WRONG_SHAPE:
        return (
            "Your previous answer was JSON but not in the required shape "
            '{"pages": [{"number": <integer>, "markdown": <string>}]}. '
            "Answer again in exactly that shape."
        )

    faults = _faults(check, offset=0, extra_place="in the attached PDF")
    return (
        f"Your previous answer had the wrong pages: {faults}. The attached PDF has {count} "
        f"pages: return exactly one item for each page number from 1 to {count}, in order, "
        "each number once."
    )


def failure_hint(check: ChunkCheck, first: int, count: int, tries: int) -> str:
    """The failed card's message: which pages, what went wrong, and what the person can do."""
    last = first + count - 1
    pages = f"page {first}" if count == 1 else f"pages {first}-{last}"

    if check.problem is AnswerProblem.NOT_JSON:
        reason = "its answer was not valid JSON"
    elif check.problem is AnswerProblem.WRONG_SHAPE:
        reason = "its answer was not in the expected format"
    else:
        reason = _faults(check, offset=first - 1, extra_place="in the PDF")

    return (
        f"The model's answer for {pages} didn't match the PDF after {tries} tries: {reason}. "
        "Retry, or reparse with another parser."
    )


def _faults(check: ChunkCheck, offset: int, extra_place: str) -> str:
    parts = []
    if check.missing:
        parts.append(f"{_pages(check.missing, offset)} {_was(check.missing)} missing")
    if check.repeated:
        parts.append(f"{_pages(check.repeated, offset)} appeared more than once")
    if check.extra:
        parts.append(f"{_pages(check.extra, offset)} {_is(check.extra)} not {extra_place}")
    return "; ".join(parts)


def _pages(numbers: tuple[int, ...], offset: int) -> str:
    shown = [str(number + offset) for number in numbers]
    if len(shown) == 1:
        return f"page {shown[0]}"
    return f"pages {', '.join(shown[:-1])} and {shown[-1]}"


def _was(numbers: tuple[int, ...]) -> str:
    return "was" if len(numbers) == 1 else "were"


def _is(numbers: tuple[int, ...]) -> str:
    return "is" if len(numbers) == 1 else "are"
