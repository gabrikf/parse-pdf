"""Render every expected failure as the envelope with its status (door 3)."""

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException

from app.core.envelope import failure
from app.core.errors import AppError
from app.documents.domain.errors import DomainError

DOMAIN_STATUS = {
    "document_not_found": 404,
    "document_busy": 409,
    "not_reparsable": 409,
    "not_dead": 409,
    "not_ready": 409,
    "model_budget_exhausted": 429,
}
HTTP_CODES = {404: "not_found", 405: "method_not_allowed"}


async def _app_error(_request: Request, exc: Exception) -> JSONResponse:
    assert isinstance(exc, AppError)  # noqa: S101 - registered for AppError only
    body = failure(exc.code, exc.message, exc.details)
    return JSONResponse(body, status_code=exc.status, headers=exc.headers)


async def _domain_error(_request: Request, exc: Exception) -> JSONResponse:
    assert isinstance(exc, DomainError)  # noqa: S101 - registered for DomainError only
    return JSONResponse(failure(exc.code, exc.message), status_code=DOMAIN_STATUS[exc.code])


async def _validation_error(_request: Request, exc: Exception) -> JSONResponse:
    assert isinstance(exc, RequestValidationError)  # noqa: S101 - registered for it only
    fields = [".".join(str(part) for part in error["loc"]) for error in exc.errors()]
    body = failure("invalid_request", "The request is not valid.", {"fields": fields})
    return JSONResponse(body, status_code=422)


async def _http_error(_request: Request, exc: Exception) -> JSONResponse:
    assert isinstance(exc, HTTPException)  # noqa: S101 - registered for HTTPException only
    code = HTTP_CODES.get(exc.status_code, "http_error")
    return JSONResponse(failure(code, str(exc.detail)), status_code=exc.status_code)


def register_error_handlers(app: FastAPI) -> None:
    """Attach the handlers; unexpected exceptions go to the error boundary middleware."""
    app.add_exception_handler(AppError, _app_error)
    app.add_exception_handler(DomainError, _domain_error)
    app.add_exception_handler(RequestValidationError, _validation_error)
    app.add_exception_handler(HTTPException, _http_error)
