"""Build a worker's use case on the real Redis and bucket, with a chosen chat model."""

from redis.asyncio import Redis
from types_aiobotocore_s3 import S3Client

from app.core.clock import SystemClock
from app.core.settings import Settings
from app.models.chat_model import ChatModel
from app.worker_container import WorkerParts, build_worker_parts

__all__ = ["WorkerParts", "build_worker"]


def build_worker(
    redis: Redis,
    s3: S3Client,
    settings: Settings,
    chat: ChatModel,
    consumer: str = "test-worker",
) -> WorkerParts:
    """The production wiring, minus HTTP: ``chat`` replaces OpenRouter."""
    return build_worker_parts(settings, redis, s3, chat, clock=SystemClock(), consumer=consumer)
