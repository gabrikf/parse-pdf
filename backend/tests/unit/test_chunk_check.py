"""Criterion 43: a chunk answer's problem is named for the model and for the person (AD-056)."""

import json

import pytest

from app.parsers.chunk_check import AnswerProblem, ChunkCheck, correction, failure_hint
from app.parsers.page_schema import check_chunk_answer


def _answer(*numbers: int) -> str:
    return json.dumps({"pages": [{"number": n, "markdown": f"p{n}"} for n in numbers]})


def test_a_valid_answer_gives_the_texts_in_page_order() -> None:
    check = check_chunk_answer(_answer(3, 1, 2), 3)

    assert check == ChunkCheck(texts=["p1", "p2", "p3"])


@pytest.mark.parametrize("raw", ["not json", '{"pages": [', ""])
def test_text_that_is_not_json_is_not_json(raw: str) -> None:
    assert check_chunk_answer(raw, 2).problem is AnswerProblem.NOT_JSON


@pytest.mark.parametrize(
    "raw",
    [
        "{}",
        "[]",
        '{"pages": 3}',
        '{"pages": [{"number": "one", "markdown": "a"}]}',
        '{"pages": [{"markdown": "a"}]}',
    ],
    ids=["no pages", "a list", "pages not a list", "number not a number", "no number"],
)
def test_json_in_another_shape_is_the_wrong_shape(raw: str) -> None:
    assert check_chunk_answer(raw, 1).problem is AnswerProblem.WRONG_SHAPE


def test_missing_repeated_and_extra_pages_are_each_named() -> None:
    check = check_chunk_answer(_answer(1, 1, 4, 3), 3)

    assert check.problem is AnswerProblem.WRONG_PAGES
    assert (check.missing, check.repeated, check.extra) == ((2,), (1,), (4,))
    assert check.texts is None


def test_a_page_outside_the_chunk_repeated_is_extra_not_repeated() -> None:
    check = check_chunk_answer(_answer(1, 2, 9, 9), 2)

    assert (check.missing, check.repeated, check.extra) == ((), (), (9,))


def test_the_correction_lists_every_fault_in_chunk_numbers() -> None:
    check = ChunkCheck(problem=AnswerProblem.WRONG_PAGES, missing=(2, 3), repeated=(1,), extra=(5,))

    assert correction(check, 3) == (
        "Your previous answer had the wrong pages: pages 2 and 3 were missing; page 1 appeared "
        "more than once; page 5 is not in the attached PDF. The attached PDF has 3 pages: "
        "return exactly one item for each page number from 1 to 3, in order, each number once."
    )


def test_the_correction_for_text_that_is_not_json_asks_for_only_the_object() -> None:
    message = correction(ChunkCheck(problem=AnswerProblem.NOT_JSON), 2)

    assert message == (
        "Your previous answer was not valid JSON; it may have been cut off. Answer again with "
        "only the JSON object, every page complete, and no text outside it."
    )


def test_the_correction_for_the_wrong_shape_spells_out_the_shape() -> None:
    message = correction(ChunkCheck(problem=AnswerProblem.WRONG_SHAPE), 2)

    assert '{"pages": [{"number": <integer>, "markdown": <string>}]}' in message


@pytest.mark.parametrize(
    ("check", "first", "count", "expected"),
    [
        (
            ChunkCheck(problem=AnswerProblem.NOT_JSON),
            11,
            10,
            "for pages 11-20 didn't match the PDF after 3 tries: its answer was not valid JSON.",
        ),
        (
            ChunkCheck(problem=AnswerProblem.WRONG_SHAPE),
            7,
            1,
            "for page 7 didn't match the PDF after 3 tries: its answer was not in the expected "
            "format.",
        ),
        (
            ChunkCheck(problem=AnswerProblem.WRONG_PAGES, repeated=(1, 2, 3), extra=(4,)),
            4,
            3,
            "for pages 4-6 didn't match the PDF after 3 tries: pages 4, 5 and 6 appeared more "
            "than once; page 7 is not in the PDF.",
        ),
    ],
    ids=["not json", "wrong shape", "repeated and extra"],
)
def test_the_hint_uses_document_page_numbers(
    check: ChunkCheck, first: int, count: int, expected: str
) -> None:
    hint = failure_hint(check, first, count, 3)

    assert hint == f"The model's answer {expected} Retry, or reparse with another parser."
