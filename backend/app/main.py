"""FastAPI application factory: middleware order, routers, lifespan."""

from collections.abc import AsyncIterator, Callable
from contextlib import AbstractAsyncContextManager, asynccontextmanager

from fastapi import FastAPI

from app.container import api_container
from app.core.logging import configure_logging
from app.core.settings import Settings, get_settings
from app.documents.controllers import (
    budget_controller,
    documents_controller,
    health_controller,
    sessions_controller,
    upload_controller,
)
from app.documents.controllers.api_services import ApiServices
from app.documents.controllers.error_handlers import register_error_handlers
from app.security.body_limit import BodyLimitMiddleware
from app.security.cors import page_cors
from app.security.error_boundary import ErrorBoundaryMiddleware
from app.security.headers import security_headers
from app.security.request_id import RequestIdMiddleware

ContainerFactory = Callable[[Settings], AbstractAsyncContextManager[ApiServices]]


def create_app(
    settings: Settings | None = None, container: ContainerFactory = api_container
) -> FastAPI:
    """Build the app. Middleware, outermost first: request id, security headers, CORS,
    body limit, error boundary - so even a 500 carries the headers and the request id.
    """
    config = settings or get_settings()
    configure_logging(config.log_level)

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        async with container(config) as services:
            app.state.services = services
            yield

    app = FastAPI(
        title="parse-pdf",
        version="1.0.0",
        lifespan=lifespan,
        docs_url="/api/v1/docs",
        openapi_url="/api/v1/openapi.json",
        redoc_url=None,
    )
    register_error_handlers(app)
    for router in (
        sessions_controller.router,
        upload_controller.router,
        documents_controller.router,
        budget_controller.router,
        health_controller.router,
    ):
        app.include_router(router)

    app.add_middleware(ErrorBoundaryMiddleware)
    app.add_middleware(BodyLimitMiddleware)
    app.add_middleware(page_cors, page_origin=config.page_origin)
    app.add_middleware(security_headers)
    app.add_middleware(RequestIdMiddleware)
    return app
