"""CORS for the page's origin only, with credentials; never ``*`` (AD-006)."""

from starlette.middleware.cors import CORSMiddleware

from app.security.asgi_types import ASGIApp


def page_cors(app: ASGIApp, page_origin: str) -> CORSMiddleware:
    """Echo ``PAGE_ORIGIN`` in ``Access-Control-Allow-Origin``; any other origin gets nothing."""
    return CORSMiddleware(
        app,
        allow_origins=[page_origin],
        allow_credentials=True,
        allow_methods=["GET", "POST", "DELETE"],
        allow_headers=["Content-Type", "Authorization", "X-Request-ID"],
        expose_headers=["X-Request-ID", "Retry-After"],
        max_age=600,
    )
