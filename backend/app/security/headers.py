"""Security headers from ``secure`` ``Preset.BASIC`` on every response (door 9, AD-007)."""

from secure import Preset, Secure
from secure.middleware import SecureASGIMiddleware

from app.security.asgi_types import ASGIApp


def security_headers(app: ASGIApp) -> SecureASGIMiddleware:
    """Wrap ``app`` so every HTTP response carries the BASIC preset."""
    return SecureASGIMiddleware(app, secure=Secure.from_preset(Preset.BASIC))
