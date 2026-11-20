"""Criterion 46: a scanned PDF reaches ``ready`` with markdown pages through both model parsers.

The worker runs its production wiring (``worker_loop``: OpenRouter client, call gate, retry
policy) against the local OpenRouter stub, so the request leaves over real HTTP.
"""

import asyncio
from collections.abc import Iterator

import httpx
import pytest
from redis.asyncio import Redis

from app.worker_container import worker_loop
from stubs.openrouter_stub import CALLS
from tests.conftest import make_settings
from tests.integration.harness import pdf_part, upload
from tests.integration.stub_server import running_stub
from tests.pdf_factory import make_image_pdf

GEMINI = "google/gemini-3.1-flash-lite"
GUARD = "meta-llama/llama-guard-4-12b"


@pytest.fixture(scope="module")
def stub_url() -> Iterator[str]:
    with running_stub() as url:
        yield url


async def _wait_final(client: httpx.AsyncClient, document_id: str) -> dict[str, object]:
    data: dict[str, object] = {}
    for _ in range(150):
        data = (await client.get(f"/api/v1/documents/{document_id}")).json()["data"]
        if data["status"] not in {"queued", "processing"}:
            break
        await asyncio.sleep(0.1)
    return data


@pytest.mark.parametrize(
    ("parser", "parse_model"),
    [("gemini-3.1-flash-lite", GEMINI), ("gpt-5-mini", "openai/gpt-5-mini")],
    ids=["gemini-3.1-flash-lite", "gpt-5-mini"],
)
async def test_scanned_pdf_reaches_ready_with_markdown_pages(
    session_client: httpx.AsyncClient, redis: Redis, stub_url: str, parser: str, parse_model: str
) -> None:
    del redis
    CALLS.clear()
    settings = make_settings(openrouter_base_url=stub_url, openrouter_api_key="stub-key")
    response = await upload(session_client, [pdf_part("scan.pdf", make_image_pdf(3))], parser)
    assert response.status_code == 202, response.text
    document_id = response.json()["data"]["documents"][0]["id"]
    stop = asyncio.Event()

    async with worker_loop(settings) as loop:
        task = asyncio.create_task(loop.run(stop))
        document = await _wait_final(session_client, document_id)
        stop.set()
        await task

    assert document["status"] == "ready", document
    assert document["parser"] == parser
    pages = (await session_client.get(f"/api/v1/documents/{document_id}/pages")).json()["data"]
    assert [page["number"] for page in pages] == [1, 2, 3]
    assert all(page["format"] == "markdown" for page in pages)
    assert all(page["content"].strip() for page in pages)
    assert CALLS[0] == parse_model, "the page call goes to the parser's own model"
    assert set(CALLS) == {parse_model, GEMINI, GUARD}
