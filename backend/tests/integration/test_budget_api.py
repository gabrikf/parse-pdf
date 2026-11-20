"""Criterion 45: the daily model page budget, on upload, reparse and the next UTC day."""

from datetime import UTC, datetime, timedelta

import httpx
from redis.asyncio import Redis

from app.documents.domain.document_status import DocumentStatus
from app.rate_limit.redis_model_budget import RedisModelBudget
from tests.fakes import FakeClock
from tests.integration.harness import pdf_part, upload
from tests.integration.seed import seed
from tests.pdf_factory import make_text_pdf


def _today_key() -> str:
    return f"budget:model_pages:{datetime.now(UTC).date().isoformat()}"


async def _session_id(client: httpx.AsyncClient) -> str:
    response = await client.post("/api/v1/sessions")
    session_id: str = response.json()["data"]["session_id"]
    return session_id


async def test_2990_used_plus_10_pages_is_accepted_and_reaches_3000(
    session_client: httpx.AsyncClient, redis: Redis
) -> None:
    await redis.set(_today_key(), 2990)

    response = await upload(
        session_client, [pdf_part("ten.pdf", make_text_pdf(10))], parser="gemini-3.1-flash-lite"
    )

    assert response.status_code == 202, response.text
    assert len(response.json()["data"]["documents"]) == 1
    assert await redis.get(_today_key()) == "3000"


async def test_2990_used_plus_11_pages_is_refused_and_not_stored(
    session_client: httpx.AsyncClient, redis: Redis
) -> None:
    await redis.set(_today_key(), 2990)

    response = await upload(
        session_client,
        [pdf_part("eleven.pdf", make_text_pdf(11)), pdf_part("one.pdf", make_text_pdf(1))],
        parser="gpt-5-mini",
    )

    body = response.json()["data"]
    assert response.status_code == 202, response.text
    assert [item["code"] for item in body["rejected"]] == ["model_budget_exhausted"]
    assert [item["filename"] for item in body["documents"]] == ["one.pdf"]
    assert await redis.get(_today_key()) == "2991"


async def test_pypdf_is_never_refused_by_the_budget(
    session_client: httpx.AsyncClient, redis: Redis
) -> None:
    await redis.set(_today_key(), 3000)

    response = await upload(session_client, [pdf_part("p.pdf", make_text_pdf(11))])

    assert response.status_code == 202, response.text
    assert response.json()["data"]["rejected"] == []


async def test_reparse_past_the_budget_is_429(
    session_client: httpx.AsyncClient, redis: Redis
) -> None:
    session_id = await _session_id(session_client)
    document = await seed(redis, session_id, 0, DocumentStatus.READY)
    await redis.set(_today_key(), 3000)

    response = await session_client.post(
        f"/api/v1/documents/{document.id}/reparse", json={"parser": "gpt-5-mini"}
    )

    assert response.status_code == 429
    assert response.json()["error"]["code"] == "model_budget_exhausted"
    assert await redis.hget(f"doc:{document.id}", "status") == "ready"


async def test_next_utc_day_starts_at_0(redis: Redis) -> None:
    clock = FakeClock(datetime(2026, 11, 19, 23, 59, tzinfo=UTC))
    budget = RedisModelBudget(redis, clock, 3000)
    assert await budget.reserve(3000) is True
    assert await budget.reserve(1) is False

    clock.advance(timedelta(minutes=2).total_seconds())

    usage = await budget.usage()
    assert usage.used == 0
    assert usage.resets_at == datetime(2026, 11, 21, tzinfo=UTC)
    assert await budget.reserve(1) is True
