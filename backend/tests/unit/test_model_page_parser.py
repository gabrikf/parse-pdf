"""Criteria 42-44: 10-page chunks sent as PDF files, validated answers, checkpoint resume."""

import json
from dataclasses import dataclass, field

import pytest

from app.core.clock import SystemClock
from app.core.isolated import IsolatedRunner
from app.documents.domain.document import Document
from app.documents.domain.document_status import DocumentStatus
from app.documents.domain.job_errors import PermanentFailure
from app.documents.domain.page import Page, PageFormat
from app.documents.domain.parser_kind import ParserKind
from app.models.chat_model import ChatRequest
from app.parsers.model_page_parser import ModelPageParser
from app.parsers.page_parser import ParseRequest
from app.parsers.page_schema import read_chunk_pages
from tests.pdf_factory import make_text_pdf

MODEL = "openai/gpt-5-mini"
NOW = SystemClock().now()


@dataclass
class PagesChat:
    """Answers each chunk with valid JSON unless ``bad_answers`` says otherwise."""

    bad_answers: list[str] = field(default_factory=list)
    calls: list[ChatRequest] = field(default_factory=list)

    async def complete(self, request: ChatRequest) -> str:
        self.calls.append(request)
        if self.bad_answers:
            return self.bad_answers.pop(0)
        text = request.messages[1]["content"][0]["text"]
        count = int(text.split(" has ")[1].split(" ")[0])
        return json.dumps(
            {"pages": [{"number": n, "markdown": f"# p{n}"} for n in range(1, count + 1)]}
        )


@dataclass
class MemoryCheckpoint:
    saved: dict[int, list[Page]] = field(default_factory=dict)

    async def load(self) -> dict[int, list[Page]]:
        return dict(self.saved)

    async def save(self, index: int, pages: list[Page]) -> None:
        self.saved[index] = pages


def _request(pages: int, checkpoint: MemoryCheckpoint) -> ParseRequest:
    document = Document(
        id="d1",
        session_id="s1",
        filename="a.pdf",
        parser=ParserKind.GPT5_MINI,
        status=DocumentStatus.PROCESSING,
        page_count=pages,
        size_bytes=1,
        created_at=NOW,
        updated_at=NOW,
        run_id="r1",
    )
    return ParseRequest(document, make_text_pdf(pages), checkpoint)


def _parser(chat: PagesChat) -> ModelPageParser:
    return ModelPageParser(chat, IsolatedRunner(1), MODEL, 60)


def _chunk_sizes(chat: PagesChat) -> list[int]:
    return [
        int(call.messages[1]["content"][0]["text"].split(" has ")[1].split(" ")[0])
        for call in chat.calls
    ]


async def test_23_pages_take_calls_of_10_10_3_and_return_markdown_pages() -> None:
    chat = PagesChat()

    pages = await _parser(chat).parse(_request(23, MemoryCheckpoint()))

    assert _chunk_sizes(chat) == [10, 10, 3]
    assert [page.number for page in pages] == list(range(1, 24))
    assert {page.format for page in pages} == {PageFormat.MARKDOWN}
    assert pages[10].content == "# p1"


async def test_10_pages_take_one_call() -> None:
    chat = PagesChat()

    await _parser(chat).parse(_request(10, MemoryCheckpoint()))

    assert len(chat.calls) == 1


async def test_request_sends_a_pdf_file_part_native_engine_and_json_schema() -> None:
    chat = PagesChat()

    await _parser(chat).parse(_request(1, MemoryCheckpoint()))

    call = chat.calls[0]
    assert call.model == MODEL
    file_part = call.messages[1]["content"][1]
    assert file_part["type"] == "file"
    assert file_part["file"]["file_data"].startswith("data:application/pdf;base64,JVBERi")
    assert call.plugins == [{"id": "file-parser", "pdf": {"engine": "native"}}]
    assert call.response_format is not None
    assert call.response_format["type"] == "json_schema"


async def test_resumed_job_sends_only_missing_chunks() -> None:
    checkpoint = MemoryCheckpoint()
    first = PagesChat()
    await _parser(first).parse(_request(23, checkpoint))
    del checkpoint.saved[2]
    resumed = PagesChat()

    pages = await _parser(resumed).parse(_request(23, checkpoint))

    assert _chunk_sizes(resumed) == [3]
    assert len(pages) == 23


@pytest.mark.parametrize(
    "bad",
    [
        json.dumps({"pages": [{"number": 1, "markdown": "a"}]}),
        json.dumps({"pages": [{"number": 1, "markdown": "a"}, {"number": 1, "markdown": "b"}]}),
        json.dumps({"pages": [{"number": n, "markdown": "a"} for n in (1, 2, 3)]}),
        "not json",
    ],
    ids=["missing", "repeated", "added", "not json"],
)
async def test_invalid_answer_is_retried_twice_then_dead(bad: str) -> None:
    chat = PagesChat(bad_answers=[bad, bad, bad])

    with pytest.raises(PermanentFailure) as caught:
        await _parser(chat).parse(_request(2, MemoryCheckpoint()))

    assert caught.value.code == "model_output_invalid"
    assert len(chat.calls) == 3


async def test_one_invalid_answer_then_valid_succeeds() -> None:
    chat = PagesChat(bad_answers=["{}"])

    pages = await _parser(chat).parse(_request(2, MemoryCheckpoint()))

    assert len(chat.calls) == 2
    assert len(pages) == 2


def test_page_schema_accepts_fenced_json_and_reorders() -> None:
    raw = (
        '```json\n{"pages": [{"number": 2, "markdown": "b"}, {"number": 1, "markdown": "a"}]}\n```'
    )

    assert read_chunk_pages(raw, 2) == ["a", "b"]


async def test_3_page_chunks_split_10_pages_into_3_3_3_1_in_order() -> None:
    """A slow model gets smaller chunks so each answer fits its call deadline (AD-055)."""
    chat = PagesChat()
    parser = ModelPageParser(chat, IsolatedRunner(1), MODEL, 60, chunk_pages=3)

    pages = await parser.parse(_request(10, MemoryCheckpoint()))

    assert _chunk_sizes(chat) == [3, 3, 3, 1]
    assert [page.number for page in pages] == list(range(1, 11))


async def test_each_chunk_call_carries_the_reasoning_effort_and_call_deadline() -> None:
    chat = PagesChat()
    parser = ModelPageParser(
        chat, IsolatedRunner(1), MODEL, 60, reasoning_effort="minimal", call_timeout_s=120.0
    )

    await parser.parse(_request(1, MemoryCheckpoint()))

    assert chat.calls[0].reasoning_effort == "minimal"
    assert chat.calls[0].timeout_s == 120.0


async def test_a_resumed_3_page_job_sends_only_the_chunks_left() -> None:
    chat = PagesChat()
    checkpoint = MemoryCheckpoint()
    checkpoint.saved[0] = [Page(n, f"# p{n}", PageFormat.MARKDOWN) for n in (1, 2, 3)]
    parser = ModelPageParser(chat, IsolatedRunner(1), MODEL, 60, chunk_pages=3)

    pages = await parser.parse(_request(7, checkpoint))

    assert _chunk_sizes(chat) == [3, 1]
    assert [page.number for page in pages] == list(range(1, 8))


async def test_a_checkpoint_saved_under_another_chunk_size_is_parsed_again() -> None:
    """10-page chunk 0 saved before a deploy cut chunks to 3: it is not reused as pages 1-3."""
    chat = PagesChat()
    checkpoint = MemoryCheckpoint()
    checkpoint.saved[0] = [Page(n, f"# old {n}", PageFormat.MARKDOWN) for n in range(1, 11)]
    parser = ModelPageParser(chat, IsolatedRunner(1), MODEL, 60, chunk_pages=3)

    pages = await parser.parse(_request(10, checkpoint))

    assert _chunk_sizes(chat) == [3, 3, 3, 1]
    assert [page.number for page in pages] == list(range(1, 11))
    assert all("old" not in page.content for page in pages)


async def test_a_retry_tells_the_model_what_its_last_answer_got_wrong() -> None:
    """AD-056: the second call carries the reason, in chunk-local page numbers."""
    missing_page_2 = json.dumps({"pages": [{"number": 1, "markdown": "a"}]})
    chat = PagesChat(bad_answers=[missing_page_2])

    pages = await _parser(chat).parse(_request(2, MemoryCheckpoint()))

    first, retry = chat.calls
    assert len(first.messages) == 2
    assert retry.messages[:2] == first.messages
    assert retry.messages[2] == {
        "role": "user",
        "content": (
            "Your previous answer had the wrong pages: page 2 was missing. The attached PDF has "
            "2 pages: return exactly one item for each page number from 1 to 2, in order, each "
            "number once."
        ),
    }
    assert [page.number for page in pages] == [1, 2]


async def test_each_retry_carries_only_the_latest_problem() -> None:
    chat = PagesChat(bad_answers=["not json", "{}"])

    await _parser(chat).parse(_request(2, MemoryCheckpoint()))

    second, third = chat.calls[1], chat.calls[2]
    assert len(second.messages) == len(third.messages) == 3
    assert second.messages[2]["content"].startswith("Your previous answer was not valid JSON")
    assert third.messages[2]["content"].startswith(
        "Your previous answer was JSON but not in the required shape"
    )


async def test_after_3_wrong_answers_the_hint_names_the_document_pages_and_the_problem() -> None:
    """Chunk 2 of a 5-page job under 3-page chunks is pages 4-5; its page 2 is page 5."""
    only_page_1 = json.dumps({"pages": [{"number": 1, "markdown": "a"}]})
    chat = PagesChat(bad_answers=[])
    parser = ModelPageParser(chat, IsolatedRunner(1), MODEL, 60, chunk_pages=3)
    checkpoint = MemoryCheckpoint()
    checkpoint.saved[0] = [Page(n, f"# p{n}", PageFormat.MARKDOWN) for n in (1, 2, 3)]
    chat.bad_answers.extend([only_page_1] * 3)

    with pytest.raises(PermanentFailure) as caught:
        await parser.parse(_request(5, checkpoint))

    assert caught.value.code == "model_output_invalid"
    assert caught.value.hint == (
        "The model's answer for pages 4-5 didn't match the PDF after 3 tries: page 5 was "
        "missing. Retry, or reparse with another parser."
    )
