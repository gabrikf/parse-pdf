"""Criteria 32-33: how OpenRouter answers are classified and retried (respx, no network)."""

import asyncio
import json
from collections.abc import AsyncIterator
from datetime import timedelta
from email.utils import format_datetime

import httpx
import pytest
import respx

from app.documents.domain.job_errors import PermanentFailure, TransientFailure
from app.models.call_gate import ModelCallGate
from app.models.chat_model import ChatRequest
from app.models.openrouter_chat_model import OpenRouterChatModel, parse_retry_after
from app.models.retry_policy import RetryPolicy
from app.rate_limit.rate_limiter import RateDecision
from tests.fakes import FakeClock

BASE = "https://openrouter.test/api/v1"
REQUEST = ChatRequest(
    model="google/gemini-3.1-flash-lite", messages=[{"role": "user", "content": "x"}]
)
OK_BODY = {"choices": [{"message": {"content": "hello"}}]}


class OpenLimiter:
    async def hit(self, key: str, limit: int, window_s: int) -> RateDecision:
        return RateDecision(allowed=True)


@pytest.fixture
async def http() -> AsyncIterator[httpx.AsyncClient]:
    async with httpx.AsyncClient(base_url=BASE) as client:
        yield client


def _model(http: httpx.AsyncClient, sleeps: list[float], api_key: str = "k") -> OpenRouterChatModel:
    async def sleep(seconds: float) -> None:
        sleeps.append(seconds)

    retry = RetryPolicy(sleep=sleep, jitter=lambda low, high: 0.0)
    gate = ModelCallGate(OpenLimiter(), 30)
    return OpenRouterChatModel(http, api_key, gate, retry, clock=FakeClock())


@respx.mock
async def test_429_429_200_returns_after_three_calls(http: httpx.AsyncClient) -> None:
    route = respx.post(f"{BASE}/chat/completions").mock(
        side_effect=[httpx.Response(429), httpx.Response(429), httpx.Response(200, json=OK_BODY)]
    )

    assert await _model(http, []).complete(REQUEST) == "hello"
    assert route.call_count == 3


@respx.mock
async def test_retry_after_7_waits_at_least_7s(http: httpx.AsyncClient) -> None:
    respx.post(f"{BASE}/chat/completions").mock(
        side_effect=[
            httpx.Response(429, headers={"Retry-After": "7"}),
            httpx.Response(200, json=OK_BODY),
        ]
    )
    sleeps: list[float] = []

    await _model(http, sleeps).complete(REQUEST)

    assert sleeps == [7.0]


@respx.mock
async def test_six_429s_raise_transient(http: httpx.AsyncClient) -> None:
    route = respx.post(f"{BASE}/chat/completions").mock(return_value=httpx.Response(429))

    with pytest.raises(TransientFailure):
        await _model(http, []).complete(REQUEST)
    assert route.call_count == 6


@respx.mock
@pytest.mark.parametrize("status", [500, 502, 503])
async def test_5xx_is_retried(http: httpx.AsyncClient, status: int) -> None:
    route = respx.post(f"{BASE}/chat/completions").mock(
        side_effect=[httpx.Response(status), httpx.Response(200, json=OK_BODY)]
    )

    assert await _model(http, []).complete(REQUEST) == "hello"
    assert route.call_count == 2


@respx.mock
async def test_timeout_is_retried(http: httpx.AsyncClient) -> None:
    route = respx.post(f"{BASE}/chat/completions").mock(
        side_effect=[httpx.ReadTimeout("slow"), httpx.Response(200, json=OK_BODY)]
    )

    assert await _model(http, []).complete(REQUEST) == "hello"
    assert route.call_count == 2


@respx.mock
async def test_connection_error_is_retried(http: httpx.AsyncClient) -> None:
    route = respx.post(f"{BASE}/chat/completions").mock(
        side_effect=[httpx.ConnectError("down"), httpx.Response(200, json=OK_BODY)]
    )

    assert await _model(http, []).complete(REQUEST) == "hello"
    assert route.call_count == 2


@respx.mock
@pytest.mark.parametrize(
    ("status", "code"),
    [
        (400, "provider_rejected"),
        (401, "provider_rejected"),
        (403, "provider_rejected"),
        (404, "provider_rejected"),
        (402, "provider_out_of_credits"),
    ],
)
async def test_permanent_statuses_are_not_retried(
    http: httpx.AsyncClient, status: int, code: str
) -> None:
    route = respx.post(f"{BASE}/chat/completions").mock(return_value=httpx.Response(status))

    with pytest.raises(PermanentFailure) as caught:
        await _model(http, []).complete(REQUEST)
    assert caught.value.code == code
    assert route.call_count == 1


@respx.mock
async def test_empty_key_is_not_configured_with_no_call(http: httpx.AsyncClient) -> None:
    route = respx.post(f"{BASE}/chat/completions").mock(return_value=httpx.Response(200))

    with pytest.raises(PermanentFailure) as caught:
        await _model(http, [], api_key="").complete(REQUEST)
    assert caught.value.code == "provider_not_configured"
    assert route.call_count == 0


@respx.mock
@pytest.mark.parametrize(
    "body",
    [{"choices": []}, {"choices": [{"message": {"content": "  "}}]}, {"error": "x"}],
)
async def test_200_without_content_is_retried(
    http: httpx.AsyncClient, body: dict[str, object]
) -> None:
    route = respx.post(f"{BASE}/chat/completions").mock(
        side_effect=[httpx.Response(200, json=body), httpx.Response(200, json=OK_BODY)]
    )

    assert await _model(http, []).complete(REQUEST) == "hello"
    assert route.call_count == 2


@respx.mock
async def test_200_with_invalid_json_is_retried(http: httpx.AsyncClient) -> None:
    route = respx.post(f"{BASE}/chat/completions").mock(
        side_effect=[httpx.Response(200, text="<html>"), httpx.Response(200, json=OK_BODY)]
    )

    assert await _model(http, []).complete(REQUEST) == "hello"
    assert route.call_count == 2


@respx.mock
async def test_payload_carries_model_messages_format_plugins_and_key(
    http: httpx.AsyncClient,
) -> None:
    route = respx.post(f"{BASE}/chat/completions").mock(
        return_value=httpx.Response(200, json=OK_BODY)
    )
    request = ChatRequest(
        model="openai/gpt-5-mini",
        messages=[{"role": "user", "content": "x"}],
        response_format={"type": "json_schema"},
        plugins=[{"id": "file-parser"}],
    )

    await _model(http, [], api_key="secret-key").complete(request)

    sent = route.calls[0].request
    assert sent.headers["Authorization"] == "Bearer secret-key"
    payload = json.loads(sent.content)
    assert payload["model"] == "openai/gpt-5-mini"
    assert payload["response_format"] == {"type": "json_schema"}
    assert payload["plugins"] == [{"id": "file-parser"}]


def test_retry_after_reads_seconds_and_http_dates() -> None:
    clock = FakeClock()
    later = format_datetime(clock.now() + timedelta(seconds=30), usegmt=True)

    assert parse_retry_after("7", clock) == 7.0
    assert parse_retry_after(later, clock) == pytest.approx(30.0)
    assert parse_retry_after(None, clock) is None
    assert parse_retry_after("soon", clock) is None
    assert parse_retry_after("-5", clock) == 0.0


async def test_a_call_past_the_deadline_is_a_retryable_timeout(http: httpx.AsyncClient) -> None:
    """OpenRouter trickles whitespace on slow calls; the attempt still ends at the deadline."""

    calls = 0

    async def slow(_request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        if calls == 1:
            await asyncio.sleep(5)
        return httpx.Response(200, json=OK_BODY)

    model = _model(http, [])
    model._timeout = 0.2
    with respx.mock:
        respx.post(f"{BASE}/chat/completions").mock(side_effect=slow)
        assert await model.complete(REQUEST) == "hello"
    assert calls == 2


@respx.mock
async def test_max_tokens_and_reasoning_are_sent_when_set(http: httpx.AsyncClient) -> None:
    route = respx.post(f"{BASE}/chat/completions").mock(
        return_value=httpx.Response(200, json=OK_BODY)
    )
    request = ChatRequest(model="m", messages=[], max_tokens=10, reasoning_effort="low")

    await _model(http, []).complete(request)

    payload = json.loads(route.calls[0].request.content)
    assert payload["max_tokens"] == 10
    assert payload["reasoning"] == {"effort": "low"}
