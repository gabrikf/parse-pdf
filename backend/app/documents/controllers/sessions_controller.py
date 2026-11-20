"""``POST /api/v1/sessions``: create an anonymous session, or confirm the current one."""

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from app.core.clock import to_iso
from app.core.errors import AppError
from app.documents.controllers.responses import ok
from app.documents.controllers.session_dependency import Services
from app.security.session_guard import COOKIE_NAME, presented_token
from app.security.session_token import SESSION_TTL_S, SessionGrant

router = APIRouter(prefix="/api/v1", tags=["sessions"])
SESSIONS_WINDOW_S = 60


def _body(grant: SessionGrant) -> dict[str, str]:
    return {
        "session_id": grant.session_id,
        "expires_at": to_iso(grant.expires_at),
        "token": grant.token,
    }


@router.post("/sessions")
async def create_session(request: Request, services: Services) -> JSONResponse:
    """Reuse a valid session (200) or issue a new one (201), at most 20 per IP per minute."""
    token = presented_token(request)
    current = services.tokens.verify(token) if token else None
    if current is not None:
        return ok(_body(current))

    client_ip = request.client.host if request.client else "unknown"
    limit = services.settings.sessions_per_minute_per_ip
    decision = await services.limiter.hit(
        f"ratelimit:session:{client_ip}", limit, SESSIONS_WINDOW_S
    )
    if not decision.allowed:
        raise AppError(
            429,
            "rate_limited",
            "Too many new sessions. Wait and try again.",
            {"retry_after_s": decision.retry_after_s},
            {"Retry-After": str(decision.retry_after_s)},
        )

    grant = services.tokens.issue()
    response = ok(_body(grant), status=201)
    response.set_cookie(
        COOKIE_NAME,
        grant.token,
        max_age=SESSION_TTL_S,
        httponly=True,
        samesite="lax",
        secure=services.settings.cookie_secure,
        path="/",
    )
    return response
