"""Port: the readiness checks behind ``GET /api/v1/health/ready``."""

from typing import Protocol

OK = "ok"
DOWN = "down"
NOT_CONFIGURED = "not_configured"


class HealthProbe(Protocol):
    """Reports each dependency as ``ok``, ``down`` or ``not_configured``."""

    async def check(self) -> dict[str, str]:
        """Return ``{"redis": ..., "storage": ..., "openrouter": ...}``."""
        ...
