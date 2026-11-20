"""Criterion 23: the API keeps answering ``/health/live`` while it inspects a 1000-page upload."""

import asyncio
import time

import httpx

from tests.integration.harness import pdf_part, upload
from tests.pdf_factory import make_text_pdf

LIVE_BUDGET_S = 0.5


async def test_live_answers_during_a_1000_page_upload(session_client: httpx.AsyncClient) -> None:
    pdf = make_text_pdf(1000)
    latencies: list[float] = []
    statuses: list[int] = []

    async def probe(done: asyncio.Event) -> None:
        while not done.is_set():
            started = time.perf_counter()
            response = await session_client.get("/api/v1/health/live")
            latencies.append(time.perf_counter() - started)
            statuses.append(response.status_code)
            await asyncio.sleep(0.02)

    done = asyncio.Event()
    prober = asyncio.create_task(probe(done))
    response = await upload(session_client, [pdf_part("big.pdf", pdf)])
    done.set()
    await prober

    assert response.status_code == 202, response.text
    assert response.json()["data"]["documents"][0]["status"] == "queued"
    assert response.json()["data"]["documents"][0]["page_count"] == 1000
    assert len(statuses) >= 3
    assert set(statuses) == {200}
    assert max(latencies) < LIVE_BUDGET_S
