"""Composition root of a worker process."""

import os
import socket
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import TYPE_CHECKING

from app.core.clock import Clock, SystemClock
from app.core.isolated import IsolatedRunner
from app.core.settings import Settings
from app.documents.domain.parser_kind import ParserKind
from app.documents.services.parser_selector import ParserSelector
from app.documents.services.summary_service import SummaryService
from app.documents.use_cases.process_document import ProcessDocumentUseCase
from app.infrastructure import open_http, open_redis, open_s3
from app.models.call_gate import ModelCallGate
from app.models.chat_model import ChatModel
from app.models.llama_guard import LlamaGuard
from app.models.openrouter_chat_model import OpenRouterChatModel
from app.models.retry_policy import RetryPolicy
from app.parsers.model_page_parser import ModelPageParser
from app.parsers.pypdf_page_parser import PypdfPageParser
from app.queue.redis_stream_queue import RedisStreamQueue
from app.rate_limit.redis_model_budget import RedisModelBudget
from app.rate_limit.redis_sliding_window import RedisSlidingWindow
from app.repositories.redis_document_repository import RedisDocumentRepository
from app.storage.s3_object_storage import S3ObjectStorage
from app.worker.consumer_loop import ConsumerLoop, LoopTiming

if TYPE_CHECKING:
    from redis.asyncio import Redis
    from types_aiobotocore_s3 import S3Client

PARSE_CHILDREN = 1


def consumer_name() -> str:
    """``{hostname}-{pid}``: unique per worker process (door 2)."""
    return f"{socket.gethostname()}-{os.getpid()}"


@dataclass(frozen=True)
class WorkerParts:
    """What one worker consumes with: its queue, its use case and the repository behind it."""

    queue: RedisStreamQueue
    process: ProcessDocumentUseCase
    repository: RedisDocumentRepository


def build_worker_parts(
    settings: Settings,
    redis: "Redis",
    s3: "S3Client",
    chat: ChatModel,
    *,
    clock: Clock,
    consumer: str,
) -> WorkerParts:
    """Wire the parsers, the summary and the use case around one chat model."""
    repository = RedisDocumentRepository(redis)
    queue = RedisStreamQueue(redis, consumer)
    runner = IsolatedRunner(PARSE_CHILDREN)
    timeout = settings.pypdf_parse_timeout_s
    parsers = ParserSelector(
        {
            ParserKind.PYPDF: PypdfPageParser(runner, timeout),
            ParserKind.GEMINI: ModelPageParser(
                chat,
                runner,
                settings.gemini_parser_model_id,
                timeout,
                chunk_pages=settings.gemini_parser_chunk_pages,
                reasoning_effort=settings.gemini_parser_reasoning_effort,
                call_timeout_s=settings.openrouter_parse_timeout_s,
            ),
            ParserKind.GPT5_MINI: ModelPageParser(
                chat,
                runner,
                settings.gpt_parser_model_id,
                timeout,
                chunk_pages=settings.gpt_parser_chunk_pages,
                reasoning_effort=settings.gpt_parser_reasoning_effort,
                call_timeout_s=settings.openrouter_parse_timeout_s,
            ),
        }
    )

    budget = RedisModelBudget(redis, clock, settings.model_page_budget_per_day)
    guard = LlamaGuard(chat, settings.guardrail_model_id, settings.guardrail_allowed)
    summaries = SummaryService(chat, guard, budget, settings.summary_model_id)
    process = ProcessDocumentUseCase(
        repository,
        queue,
        S3ObjectStorage(s3, settings.s3_bucket),
        parsers,
        summaries,
        clock=clock,
        max_deliveries=settings.max_deliveries,
    )
    return WorkerParts(queue=queue, process=process, repository=repository)


def loop_timing(settings: Settings) -> LoopTiming:
    """The reclaim, refresh and shutdown timings from the settings."""
    return LoopTiming(
        claim_idle_ms=settings.job_claim_idle_ms,
        sweep_s=settings.reclaim_sweep_s,
        refresh_s=settings.claim_refresh_s,
        grace_s=settings.shutdown_grace_s,
    )


@asynccontextmanager
async def worker_loop(settings: Settings) -> AsyncIterator[ConsumerLoop]:
    """Open the clients, put OpenRouter behind the shared call gate, and wire the loop."""
    clock = SystemClock()
    redis = open_redis(settings)
    try:
        async with open_s3(settings) as s3, open_http(settings) as http:
            gate = ModelCallGate(
                RedisSlidingWindow(redis, clock), settings.openrouter_calls_per_minute
            )
            chat = OpenRouterChatModel(
                http,
                settings.openrouter_api_key,
                gate,
                RetryPolicy(),
                clock=clock,
                timeout_s=settings.openrouter_timeout_s,
            )
            parts = build_worker_parts(
                settings, redis, s3, chat, clock=clock, consumer=consumer_name()
            )
            yield ConsumerLoop(parts.queue, parts.process, loop_timing(settings))
    finally:
        await redis.aclose()
