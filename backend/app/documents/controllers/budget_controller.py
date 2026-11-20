"""``GET /api/v1/budget``: today's model page budget, shown on the page's right rail."""

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from app.core.clock import to_iso
from app.documents.controllers.responses import ok
from app.documents.controllers.session_dependency import Services, Session

router = APIRouter(prefix="/api/v1", tags=["budget"])


@router.get("/budget")
async def budget(_session: Session, services: Services) -> JSONResponse:
    """``{used, limit, resets_at}`` for the current UTC day."""
    usage = await services.budget.execute()
    return ok({"used": usage.used, "limit": usage.limit, "resets_at": to_iso(usage.resets_at)})
