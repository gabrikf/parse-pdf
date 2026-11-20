"""Give every request an id, put it in logs and envelopes, and return it as ``X-Request-ID``."""

import re

from app.core.ids import new_id
from app.core.request_context import request_id_var
from app.security.asgi_types import ASGIApp, Message, Receive, Scope, Send

HEADER = b"x-request-id"
SAFE_ID = re.compile(r"^[A-Za-z0-9-]{8,64}$")


class RequestIdMiddleware:
    """Reuses a well-formed incoming id (for tracing through nginx), else makes a uuid4."""

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        """Tag the request and its response with the id."""
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        incoming = dict(scope["headers"]).get(HEADER, b"").decode("latin-1")
        request_id = incoming if SAFE_ID.match(incoming) else new_id()
        token = request_id_var.set(request_id)

        async def send_with_id(message: Message) -> None:
            if message["type"] == "http.response.start":
                headers = [(k, v) for k, v in message.get("headers", []) if k.lower() != HEADER]
                headers.append((HEADER, request_id.encode()))
                message["headers"] = headers
            await send(message)

        try:
            await self.app(scope, receive, send_with_id)
        finally:
            request_id_var.reset(token)
