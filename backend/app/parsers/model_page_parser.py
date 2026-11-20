"""``PageParser`` with a model: 10-page chunks sent as PDF files, markdown back (door 7)."""

import base64
from typing import Any

from app.core.isolated import IsolatedCrashError, IsolatedRunner, IsolatedTimeoutError
from app.documents.domain.job_errors import PermanentFailure
from app.documents.domain.page import Page, PageFormat
from app.documents.services.prompt_builder import pages_schema, parse_messages
from app.models.chat_model import ChatModel, ChatRequest
from app.parsers.chunk_check import ChunkCheck, correction, failure_hint
from app.parsers.page_parser import ParseRequest
from app.parsers.page_schema import check_chunk_answer
from app.parsers.pdf_tools import split_pdf

CHUNK_PAGES = 10
CHUNK_ATTEMPTS = 3
FILE_PARSER_PLUGIN = {"id": "file-parser", "pdf": {"engine": "native"}}
CHUNK_MAX_TOKENS = 32_000
REASONING_EFFORT = "low"


class ModelPageParser:
    """Parses chunk by chunk, checkpointing each, so a reclaimed job sends only what is left.

    A chunk whose answer misses, repeats or adds a page is asked again up to 2 more times, each
    time told what was wrong, then the document ends ``model_output_invalid`` with a hint.
    """

    def __init__(
        self,
        chat: ChatModel,
        runner: IsolatedRunner,
        model_id: str,
        split_timeout_s: float,
        *,
        chunk_pages: int = CHUNK_PAGES,
        reasoning_effort: str = REASONING_EFFORT,
        call_timeout_s: float | None = None,
    ) -> None:
        self._chat = chat
        self._runner = runner
        self._model_id = model_id
        self._split_timeout_s = split_timeout_s

        # A slow model gets smaller chunks: its answer for one chunk must fit the call deadline.
        self._chunk_pages = chunk_pages
        self._reasoning_effort = reasoning_effort
        self._call_timeout_s = call_timeout_s

    async def parse(self, request: ParseRequest) -> list[Page]:
        """Return one markdown page per PDF page."""
        chunks = await self._split(request.pdf)
        done = await request.checkpoint.load()

        pages: list[Page] = []
        for index, (chunk, count) in enumerate(chunks):
            first = index * self._chunk_pages + 1
            if not _covers(done.get(index), first, count):
                done[index] = await self._parse_chunk(chunk, count, first)
                await request.checkpoint.save(index, done[index])
            pages.extend(done[index])
        return pages

    async def _split(self, pdf: bytes) -> list[tuple[bytes, int]]:
        try:
            chunks: list[tuple[bytes, int]] = await self._runner.run(
                split_pdf, (pdf, self._chunk_pages), self._split_timeout_s
            )
        except IsolatedTimeoutError as exc:
            raise PermanentFailure("parse_timeout") from exc
        except IsolatedCrashError as exc:
            raise PermanentFailure("unreadable_pdf") from exc
        return chunks

    async def _parse_chunk(self, chunk: bytes, count: int, first: int) -> list[Page]:
        """Ask for the chunk's pages; a wrong answer is sent back to the model with the reason.

        Each retry carries one extra message saying exactly what the last answer got wrong (not
        JSON, wrong shape, or which pages were missing, repeated or extra), so the model fixes
        that instead of repeating it. After ``CHUNK_ATTEMPTS`` the document ends dead with a hint
        naming the pages and the problem (AD-056).
        """
        messages = parse_messages(base64.b64encode(chunk).decode(), count)
        check = ChunkCheck()

        for attempt in range(CHUNK_ATTEMPTS):
            feedback = [] if attempt == 0 else [_correction_message(check, count)]
            check = check_chunk_answer(
                await self._chat.complete(self._request(messages + feedback)), count
            )
            if check.texts is not None:
                return [
                    Page(first + offset, text, PageFormat.MARKDOWN)
                    for offset, text in enumerate(check.texts)
                ]

        raise PermanentFailure(
            "model_output_invalid",
            hint=failure_hint(check, first, count, CHUNK_ATTEMPTS),
        )

    def _request(self, messages: list[dict[str, Any]]) -> ChatRequest:
        return ChatRequest(
            model=self._model_id,
            messages=messages,
            response_format=pages_schema(),
            plugins=[FILE_PARSER_PLUGIN],
            max_tokens=CHUNK_MAX_TOKENS,
            reasoning_effort=self._reasoning_effort,
            timeout_s=self._call_timeout_s,
        )


def _correction_message(check: ChunkCheck, count: int) -> dict[str, Any]:
    return {"role": "user", "content": correction(check, count)}


def _covers(saved: list[Page] | None, first: int, count: int) -> bool:
    """A checkpoint is reused only if it holds exactly this chunk's pages.

    A job saved under another chunk size (a deploy changed it) would otherwise repeat or skip
    pages, so a mismatched chunk is parsed again.
    """
    if saved is None:
        return False
    return [page.number for page in saved] == list(range(first, first + count))
