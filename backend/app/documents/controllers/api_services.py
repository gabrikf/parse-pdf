"""What the controllers may use: use cases, the session service, limits and health.

The composition root (``app.container``) fills it; controllers never see an adapter.
"""

from dataclasses import dataclass

from fastapi import Request

from app.core.health import HealthProbe
from app.core.settings import Settings
from app.documents.use_cases.delete_document import DeleteDocumentUseCase
from app.documents.use_cases.read_documents import (
    GetBudgetUseCase,
    GetDocumentUseCase,
    GetPagesUseCase,
    ListDocumentsUseCase,
)
from app.documents.use_cases.rerun_documents import ReparseDocumentUseCase, RequeueDocumentUseCase
from app.documents.use_cases.upload_documents import UploadDocumentsUseCase
from app.rate_limit.rate_limiter import InFlightCounter, RateLimiter
from app.security.session_token import SessionTokenService


@dataclass(frozen=True, slots=True)
class ApiServices:
    """Everything a request handler can call."""

    settings: Settings
    tokens: SessionTokenService
    limiter: RateLimiter
    in_flight: InFlightCounter
    health: HealthProbe
    upload: UploadDocumentsUseCase
    list_documents: ListDocumentsUseCase
    get_document: GetDocumentUseCase
    get_pages: GetPagesUseCase
    reparse: ReparseDocumentUseCase
    requeue: RequeueDocumentUseCase
    delete: DeleteDocumentUseCase
    budget: GetBudgetUseCase


def api_services(request: Request) -> ApiServices:
    """FastAPI dependency: the services built at start-up."""
    services: ApiServices = request.app.state.services
    return services
