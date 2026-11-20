"""Liveness and readiness probes."""

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from app.core.envelope import success
from app.core.health import OK
from app.documents.controllers.responses import ok
from app.documents.controllers.session_dependency import Services

router = APIRouter(prefix="/api/v1/health", tags=["health"])
REQUIRED = ("redis", "storage")


@router.get("/live")
async def live() -> JSONResponse:
    """200 while the process can answer."""
    return ok({"status": "ok"})


@router.get("/ready")
async def ready(services: Services) -> JSONResponse:
    """200 when Redis and the bucket answer; 503 ``not_ready`` naming each failing check."""
    checks = await services.health.check()
    failing = [name for name in REQUIRED if checks.get(name) != OK]
    if not failing:
        return ok({"status": "ok", "checks": checks})

    body = success({"status": "not_ready", "checks": checks})
    body["error"] = {
        "code": "not_ready",
        "message": f"Not ready: {', '.join(failing)}.",
        "details": {"failing": failing},
    }
    return JSONResponse(body, status_code=503)
