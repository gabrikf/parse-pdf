"""``ChatModel`` over OpenRouter's chat completions API with plain ``httpx`` (AD-019)."""

import asyncio
from email.utils import parsedate_to_datetime
from typing import Any

import httpx

from app.core.clock import Clock
from app.documents.domain.job_errors import PermanentFailure
from app.models.call_gate import ModelCallGate
from app.models.chat_model import ChatRequest
from app.models.retry_policy import RetryableError, RetryPolicy

PERMANENT_CODES = {402: "provider_out_of_credits"}
REJECTED = "provider_rejected"
NOT_CONFIGURED = "provider_not_configured"
TOO_MANY_REQUESTS = 429
SERVER_ERROR = 500


def parse_retry_after(value: str | None, clock: Clock) -> float | None:
    """Read ``Retry-After`` as seconds or as an HTTP date."""
    if not value:
        return None
    try:
        return max(0.0, float(value))
    except ValueError:
        pass
    try:
        return max(0.0, (parsedate_to_datetime(value) - clock.now()).total_seconds())
    except (TypeError, ValueError):
        return None


def _content(body: dict[str, Any]) -> str:
    try:
        content = body["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as exc:
        raise RetryableError("response without content") from exc
    if not isinstance(content, str) or not content.strip():
        raise RetryableError("empty response")
    return content


class OpenRouterChatModel:
    """Sends one request per attempt through the call gate; classifies every failure.

    429, 5xx and timeouts are retried by ``RetryPolicy``; 402 is ``provider_out_of_credits``;
    other 4xx are ``provider_rejected``; an empty key is ``provider_not_configured``.
    """

    def __init__(
        self,
        http: httpx.AsyncClient,
        api_key: str,
        gate: ModelCallGate,
        retry: RetryPolicy,
        *,
        clock: Clock,
        timeout_s: float = 60.0,
    ) -> None:
        self._http = http
        self._api_key = api_key
        self._gate = gate
        self._retry = retry
        self._clock = clock
        self._timeout = timeout_s

    async def complete(self, request: ChatRequest) -> str:
        """Return the assistant text of ``request``."""
        if not self._api_key:
            raise PermanentFailure(NOT_CONFIGURED)
        return await self._retry.run(lambda: self._attempt(request))

    async def _attempt(self, request: ChatRequest) -> str:
        deadline = request.timeout_s or self._timeout
        async with self._gate.slot():
            try:
                # A hard deadline: OpenRouter keeps slow requests alive with whitespace, so a
                # per-read timeout alone would never fire.
                async with asyncio.timeout(deadline):
                    response = await self._http.post(
                        "/chat/completions",
                        json=self._payload(request),
                        headers={"Authorization": f"Bearer {self._api_key}"},
                        timeout=deadline,
                    )
            except (TimeoutError, httpx.TimeoutException) as exc:
                raise RetryableError("timeout") from exc
            except httpx.TransportError as exc:
                raise RetryableError("transport error") from exc
        return self._read(response)

    def _payload(self, request: ChatRequest) -> dict[str, Any]:
        payload: dict[str, Any] = {"model": request.model, "messages": request.messages}
        if request.response_format:
            payload["response_format"] = request.response_format
        if request.plugins:
            payload["plugins"] = request.plugins
        if request.max_tokens:
            payload["max_tokens"] = request.max_tokens
        if request.reasoning_effort:
            payload["reasoning"] = {"effort": request.reasoning_effort}
        return payload

    def _read(self, response: httpx.Response) -> str:
        status = response.status_code
        if status == TOO_MANY_REQUESTS or status >= SERVER_ERROR:
            retry_after = parse_retry_after(response.headers.get("Retry-After"), self._clock)
            raise RetryableError(f"status {status}", retry_after)
        if status in PERMANENT_CODES:
            raise PermanentFailure(PERMANENT_CODES[status])
        if not response.is_success:
            raise PermanentFailure(REJECTED, f"status {status}")
        try:
            body = response.json()
        except ValueError as exc:
            raise RetryableError("invalid JSON") from exc
        return _content(body)
