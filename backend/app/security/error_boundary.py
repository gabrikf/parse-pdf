"""Turn any unexpected exception into ``500 internal_error`` inside the middleware stack.

Starlette's own last-resort handler sits outside every middleware, so its 500s would miss the
security headers and the request id; this boundary sits innermost instead. The body never
holds the exception text or a stack trace.
"""

import json

from app.core.envelope import failure
from app.core.logging import get_logger
from app.security.asgi_types import ASGIApp, Message, Receive, Scope, Send, send_json
from app.security.body_limit import RequestTooLargeError

log = get_logger("error_boundary")


class ErrorBoundaryMiddleware:
    """Logs the exception with the request id and answers the envelope."""

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        """Run the app; answer 500 if it raises before responding."""
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        started = False

        async def tracking_send(message: Message) -> None:
            nonlocal started
            started = started or message["type"] == "http.response.start"
            await send(message)

        try:
            await self.app(scope, receive, tracking_send)
        except RequestTooLargeError:
            raise
        except Exception:
            log.exception("unhandled_error", path=scope.get("path"))
            if started:
                raise
            body = failure("internal_error", "Something went wrong. Try again later.")
            await send_json(send, 500, json.dumps(body).encode())
