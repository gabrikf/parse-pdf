"""Composition root: the only place that builds adapters and hands them to use cases (door 6)."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from redis.asyncio import Redis

from app.core.clock import Clock, SystemClock
from app.core.health import DOWN, NOT_CONFIGURED, OK
from app.core.isolated import IsolatedRunner
from app.core.settings import Settings
from app.documents.controllers.api_services import ApiServices
from app.documents.services.pdf_inspector import PdfInspector
from app.documents.services.pdf_validation import MAX_PAGES
from app.documents.use_cases.delete_document import DeleteDocumentUseCase
from app.documents.use_cases.read_documents import (
    GetBudgetUseCase,
    GetDocumentUseCase,
    GetPagesUseCase,
    ListDocumentsUseCase,
)
from app.documents.use_cases.rerun_documents import ReparseDocumentUseCase, RequeueDocumentUseCase
from app.documents.use_cases.upload_documents import UploadDocumentsUseCase
from app.infrastructure import open_redis, open_s3
from app.rate_limit.redis_model_budget import RedisModelBudget
from app.rate_limit.redis_sliding_window import RedisInFlightCounter, RedisSlidingWindow
from app.repositories.redis_document_repository import RedisDocumentRepository
from app.security.session_token import SessionTokenService
from app.storage.s3_object_storage import S3ObjectStorage


class DependencyProbe:
    """``HealthProbe`` over the real Redis and bucket."""

    def __init__(self, redis: Redis, storage: S3ObjectStorage, settings: Settings) -> None:
        self._redis = redis
        self._storage = storage
        self._settings = settings

    async def check(self) -> dict[str, str]:
        """PING Redis, HEAD the bucket, and say whether an OpenRouter key is set."""
        try:
            redis_ok = bool(await self._redis.ping())
        except Exception:  # noqa: BLE001 - any failure means not ready
            redis_ok = False
        storage_ok = await self._storage.is_ready()
        return {
            "redis": OK if redis_ok else DOWN,
            "storage": OK if storage_ok else DOWN,
            "openrouter": OK if self._settings.openrouter_api_key else NOT_CONFIGURED,
        }


def build_api_services(
    settings: Settings, redis: Redis, storage: S3ObjectStorage, clock: Clock
) -> ApiServices:
    """Wire every use case the API exposes."""
    repository = RedisDocumentRepository(redis)
    budget = RedisModelBudget(redis, clock, settings.model_page_budget_per_day)
    runner = IsolatedRunner(settings.inspect_concurrency)
    inspector = PdfInspector(runner, settings.inspect_timeout_s, MAX_PAGES)
    return ApiServices(
        settings=settings,
        tokens=SessionTokenService(settings.session_secret, clock),
        limiter=RedisSlidingWindow(redis, clock),
        in_flight=RedisInFlightCounter(redis),
        health=DependencyProbe(redis, storage, settings),
        upload=UploadDocumentsUseCase(repository, storage, inspector, budget, clock),
        list_documents=ListDocumentsUseCase(repository),
        get_document=GetDocumentUseCase(repository),
        get_pages=GetPagesUseCase(repository),
        reparse=ReparseDocumentUseCase(repository, budget, clock),
        requeue=RequeueDocumentUseCase(repository, clock),
        delete=DeleteDocumentUseCase(repository, storage),
        budget=GetBudgetUseCase(budget),
    )


@asynccontextmanager
async def api_container(settings: Settings) -> AsyncIterator[ApiServices]:
    """Open the clients for the API process, ensure the bucket, yield the services."""
    redis = open_redis(settings)
    try:
        async with open_s3(settings) as s3:
            storage = S3ObjectStorage(s3, settings.s3_bucket)
            await storage.ensure_bucket()
            yield build_api_services(settings, redis, storage, SystemClock())
    finally:
        await redis.aclose()
