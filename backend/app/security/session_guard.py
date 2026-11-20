"""Find and check the caller's session: the ``pp_session`` cookie or a Bearer token."""

from starlette.requests import HTTPConnection

from app.core.errors import AppError
from app.security.session_token import SessionGrant, SessionTokenService

COOKIE_NAME = "pp_session"
BEARER_PREFIX = "bearer "


def presented_token(connection: HTTPConnection) -> str | None:
    """Return the token the request carries; the cookie wins over the header."""
    cookie = connection.cookies.get(COOKIE_NAME)
    if cookie:
        return cookie
    header = connection.headers.get("authorization", "")
    if header.lower().startswith(BEARER_PREFIX):
        return header[len(BEARER_PREFIX) :].strip() or None
    return None


def require_session(connection: HTTPConnection, tokens: SessionTokenService) -> SessionGrant:
    """Return the session, or raise ``401 session_required``."""
    token = presented_token(connection)
    grant = tokens.verify(token) if token else None
    if grant is None:
        raise AppError(401, "session_required", "A valid session is required.")
    return grant
