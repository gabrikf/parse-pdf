"""FastAPI dependency that requires a valid session on a route."""

from typing import Annotated

from fastapi import Depends, Request

from app.documents.controllers.api_services import ApiServices, api_services
from app.security.session_guard import require_session
from app.security.session_token import SessionGrant


def current_session(
    request: Request, services: Annotated[ApiServices, Depends(api_services)]
) -> SessionGrant:
    """Return the caller's session or answer ``401 session_required``."""
    return require_session(request, services.tokens)


Session = Annotated[SessionGrant, Depends(current_session)]
Services = Annotated[ApiServices, Depends(api_services)]
