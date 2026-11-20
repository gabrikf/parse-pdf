"""Check a model's JSON answer for one chunk: every page exactly once, nothing extra."""

import json
from collections import Counter
from typing import Any

from app.parsers.chunk_check import AnswerProblem, ChunkCheck


def check_chunk_answer(raw: str, expected_pages: int) -> ChunkCheck:
    """Read the answer and say what is wrong with it, if anything.

    The answer must be JSON, in the schema's shape, with page numbers exactly
    ``1..expected_pages``, each once. The result names missing, repeated and extra pages so the
    model can be told precisely what to fix.
    """
    try:
        data: Any = json.loads(_strip_fence(raw))
    except ValueError:
        return ChunkCheck(problem=AnswerProblem.NOT_JSON)

    try:
        items = data["pages"]
        numbered = [(int(item["number"]), str(item["markdown"])) for item in items]
    except (ValueError, KeyError, TypeError):
        return ChunkCheck(problem=AnswerProblem.WRONG_SHAPE)

    return _check_numbers(numbered, expected_pages)


def read_chunk_pages(raw: str, expected_pages: int) -> list[str] | None:
    """Return the chunk's page texts in order, or None when the answer is invalid."""
    return check_chunk_answer(raw, expected_pages).texts


def _check_numbers(numbered: list[tuple[int, str]], expected_pages: int) -> ChunkCheck:
    expected = range(1, expected_pages + 1)
    seen = Counter(number for number, _ in numbered)

    missing = tuple(number for number in expected if number not in seen)
    repeated = tuple(
        sorted(number for number, times in seen.items() if times > 1 and number in expected)
    )
    extra = tuple(sorted(number for number in seen if number not in expected))

    if missing or repeated or extra:
        return ChunkCheck(
            problem=AnswerProblem.WRONG_PAGES, missing=missing, repeated=repeated, extra=extra
        )

    by_number = dict(numbered)
    return ChunkCheck(texts=[by_number[number] for number in expected])


def _strip_fence(raw: str) -> str:
    text = raw.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1] if "\n" in text else ""
        text = text.removesuffix("```").strip()
    return text
