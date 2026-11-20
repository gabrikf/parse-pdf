"""``PageParser`` with a model: 10-page chunks sent as PDF files, markdown back (door 7)."""

import base64

from app.core.isolated import IsolatedCrashError, IsolatedRunner, IsolatedTimeoutError
from app.documents.domain.job_errors import PermanentFailure
from app.documents.domain.page import Page, PageFormat
from app.documents.services.prompt_builder import pages_schema, parse_messages
from app.models.chat_model import ChatModel, ChatRequest
from app.parsers.page_parser import ParseRequest
from app.parsers.page_schema import read_chunk_pages
from app.parsers.pdf_tools import split_pdf

CHUNK_PAGES = 10
CHUNK_ATTEMPTS = 3
FILE_PARSER_PLUGIN = {"id": "file-parser", "pdf": {"engine": "native"}}
CHUNK_MAX_TOKENS = 32_000
REASONING_EFFORT = "low"


class ModelPageParser:
    """Parses chunk by chunk, checkpointing each, so a reclaimed job sends only what is left.

    A chunk whose answer misses, repeats or adds a page is asked again up to 2 more times,
    then the document ends ``model_output_invalid``.
    """

    def __init__(
        self, chat: ChatModel, runner: IsolatedRunner, model_id: str, split_timeout_s: float
    ) -> None:
        self._chat = chat
        self._runner = runner
        self._model_id = model_id
        self._split_timeout_s = split_timeout_s

    async def parse(self, request: ParseRequest) -> list[Page]:
        """Return one markdown page per PDF page."""
        chunks = await self._split(request.pdf)
        done = await request.checkpoint.load()

        pages: list[Page] = []
        for index, (chunk, count) in enumerate(chunks):
            if index not in done:
                first = index * CHUNK_PAGES + 1
                done[index] = await self._parse_chunk(chunk, count, first)
                await request.checkpoint.save(index, done[index])
            pages.extend(done[index])
        return pages

    async def _split(self, pdf: bytes) -> list[tuple[bytes, int]]:
        try:
            chunks: list[tuple[bytes, int]] = await self._runner.run(
                split_pdf, (pdf, CHUNK_PAGES), self._split_timeout_s
            )
        except IsolatedTimeoutError as exc:
            raise PermanentFailure("parse_timeout") from exc
        except IsolatedCrashError as exc:
            raise PermanentFailure("unreadable_pdf") from exc
        return chunks

    async def _parse_chunk(self, chunk: bytes, count: int, first: int) -> list[Page]:
        request = ChatRequest(
            model=self._model_id,
            messages=parse_messages(base64.b64encode(chunk).decode(), count),
            response_format=pages_schema(),
            plugins=[FILE_PARSER_PLUGIN],
            max_tokens=CHUNK_MAX_TOKENS,
            reasoning_effort=REASONING_EFFORT,
        )
        for _ in range(CHUNK_ATTEMPTS):
            texts = read_chunk_pages(await self._chat.complete(request), count)
            if texts is not None:
                return [
                    Page(first + offset, text, PageFormat.MARKDOWN)
                    for offset, text in enumerate(texts)
                ]
        raise PermanentFailure("model_output_invalid")
