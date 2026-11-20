"""Stop reading an upload body past 1,074,790,400 bytes and answer ``413`` (criterion 10).

Bytes are counted while they stream in, so a false ``Content-Length`` cannot get past it.
"""

import json

from app.core.envelope import failure
from app.security.asgi_types import ASGIApp, Message, Receive, Scope, Send, send_json

UPLOAD_BODY_LIMIT = 20 * 52_428_800 + 1_048_576
UPLOAD_PATH = "/api/v1/documents"


class RequestTooLargeError(Exception):
    """Raised from ``receive`` once the body passes the limit."""


def _too_large_body() -> bytes:
    message = "The upload is larger than 1,074,790,400 bytes."
    return json.dumps(failure("request_too_large", message)).encode()


class BodyLimitMiddleware:
    """Applies to ``POST /api/v1/documents``; other routes keep the framework defaults."""

    def __init__(self, app: ASGIApp, limit: int = UPLOAD_BODY_LIMIT) -> None:
        self.app = app
        self.limit = limit

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        """Count the body of an upload; answer 413 once it passes the limit."""
        if not (scope["type"] == "http" and scope["method"] == "POST" and _is_upload(scope)):
            await self.app(scope, receive, send)
            return

        if _declared_length(scope) > self.limit:
            await _send_413(send)
            return

        received = 0
        started = False

        async def counting_receive() -> Message:
            nonlocal received
            message = await receive()
            received += len(message.get("body", b""))
            if received > self.limit:
                raise RequestTooLargeError
            return message

        async def tracking_send(message: Message) -> None:
            nonlocal started
            started = started or message["type"] == "http.response.start"
            await send(message)

        try:
            await self.app(scope, counting_receive, tracking_send)
        except RequestTooLargeError:
            if not started:
                await _send_413(send)


def _is_upload(scope: Scope) -> bool:
    return str(scope["path"]).rstrip("/") == UPLOAD_PATH


def _declared_length(scope: Scope) -> int:
    raw = dict(scope["headers"]).get(b"content-length", b"0")
    try:
        return int(raw)
    except ValueError:
        return 0


async def _send_413(send: Send) -> None:
    await send_json(send, 413, _too_large_body())
