"""Anonymous session tokens: JWT HS256 with ``sub``, ``iat`` and a 7-day ``exp`` (door 4)."""

import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta

import jwt

from app.core.clock import Clock
from app.core.ids import new_id

SESSION_TTL_S = 604_800
ALGORITHM = "HS256"


@dataclass(frozen=True, slots=True)
class SessionGrant:
    """A session id, its signed token and when it expires."""

    session_id: str
    token: str
    expires_at: datetime


class SessionTokenService:
    """Signs and verifies session tokens; only ``HS256`` is accepted, so ``alg: none`` fails."""

    def __init__(self, secret: str, clock: Clock, ttl_s: int = SESSION_TTL_S) -> None:
        self._secret = secret
        self._clock = clock
        self._ttl_s = ttl_s

    def issue(self) -> SessionGrant:
        """Create a new session."""
        now = self._clock.now()
        expires_at = now + timedelta(seconds=self._ttl_s)
        session_id = new_id()
        claims = {"sub": session_id, "iat": now, "exp": expires_at}
        token = jwt.encode(claims, self._secret, algorithm=ALGORITHM)
        return SessionGrant(session_id=session_id, token=token, expires_at=expires_at)

    def verify(self, token: str) -> SessionGrant | None:
        """Return the grant of a valid token, or None (bad signature, expired, malformed)."""
        try:
            claims = jwt.decode(
                token,
                self._secret,
                algorithms=[ALGORITHM],
                options={"require": ["sub", "iat", "exp"]},
            )
            session_id = str(uuid.UUID(str(claims["sub"])))
        except (jwt.PyJWTError, ValueError):
            return None

        expires_at = datetime.fromtimestamp(int(claims["exp"]), tz=self._clock.now().tzinfo)
        return SessionGrant(session_id=session_id, token=token, expires_at=expires_at)
