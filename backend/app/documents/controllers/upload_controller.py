"""``POST /api/v1/documents``: the multipart upload, behind the per-session limits."""

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from starlette.datastructures import UploadFile
from starlette.exceptions import HTTPException
from starlette.formparsers import MultiPartException

from app.core.errors import AppError
from app.documents.controllers.documents_controller import require_parser
from app.documents.controllers.responses import ok
from app.documents.controllers.schemas.document_dto import document_dto, rejection_dto
from app.documents.controllers.session_dependency import Services, Session
from app.documents.use_cases.upload_documents import UploadCommand
from app.security.session_token import SessionGrant

router = APIRouter(prefix="/api/v1/documents", tags=["documents"])
MAX_FILES = 20
UPLOAD_WINDOW_S = 60


class StarletteFile:
    """``IncomingFile`` over Starlette's spooled upload."""

    def __init__(self, upload: UploadFile) -> None:
        self._upload = upload

    @property
    def filename(self) -> str | None:
        """The client's filename."""
        return self._upload.filename

    @property
    def size(self) -> int:
        """Bytes received for this part."""
        return self._upload.size or 0

    async def read_head(self, count: int) -> bytes:
        """The first ``count`` bytes, leaving the file rewound."""
        head = await self._upload.read(count)
        await self._upload.seek(0)
        return head

    async def read_all(self) -> bytes:
        """The whole file."""
        await self._upload.seek(0)
        return await self._upload.read()


async def _enforce_rate(services: Services, session: SessionGrant) -> None:
    limit = services.settings.upload_requests_per_minute
    key = f"ratelimit:upload:{session.session_id}"
    decision = await services.limiter.hit(key, limit, UPLOAD_WINDOW_S)
    if not decision.allowed:
        raise AppError(
            429,
            "rate_limited",
            "Too many uploads. Wait and try again.",
            {"retry_after_s": decision.retry_after_s},
            {"Retry-After": str(decision.retry_after_s)},
        )


@router.post("")
async def upload(request: Request, session: Session, services: Services) -> JSONResponse:
    """Judge each file on its own; ``202`` when at least one is stored."""
    await _enforce_rate(services, session)
    slot = f"inflight:upload:{session.session_id}"
    maximum = services.settings.uploads_in_flight_per_session
    if not await services.in_flight.acquire(slot, maximum):
        message = "Two uploads are already running. Wait for one to finish."
        raise AppError(429, "too_many_uploads_in_progress", message, {"maximum": maximum})

    try:
        return await _handle(request, session, services)
    finally:
        await services.in_flight.release(slot)


async def _handle(request: Request, session: SessionGrant, services: Services) -> JSONResponse:
    try:
        form = await request.form(max_files=MAX_FILES, max_fields=10)
    except (MultiPartException, HTTPException) as exc:
        # Starlette reports multipart limits as a 400 whose detail names the limit.
        detail = str(exc.detail if isinstance(exc, HTTPException) else exc)
        if detail.startswith("Too many files"):
            raise AppError(422, "too_many_files", "Up to 20 files per upload.") from None
        raise AppError(422, "invalid_multipart", "The upload body is not valid.") from None

    try:
        parser = require_parser(_text(form.get("parser")))
        files = [item for item in form.getlist("files") if isinstance(item, UploadFile)]
        if not files:
            raise AppError(422, "no_files", "Add at least one PDF.")

        password = _text(form.get("password")) or None
        command = UploadCommand(
            session.session_id, parser, [StarletteFile(f) for f in files], password
        )
        result = await services.upload.execute(command)
    finally:
        await form.close()

    rejected = [rejection_dto(item) for item in result.rejected]
    if not result.documents:
        message = "No file could be accepted."
        raise AppError(422, "all_files_rejected", message, {"rejected": rejected})

    data = {"documents": [document_dto(d) for d in result.documents], "rejected": rejected}
    return ok(data, status=202)


def _text(value: object) -> str | None:
    return value if isinstance(value, str) else None
