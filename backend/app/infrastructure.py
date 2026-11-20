"""Open the shared clients: Redis (with reconnect), S3 (path-style) and the OpenRouter HTTP pool."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import TYPE_CHECKING

import httpx
from aiobotocore.config import AioConfig
from aiobotocore.session import get_session
from redis.asyncio import Redis
from redis.asyncio.retry import Retry
from redis.backoff import ExponentialBackoff
from redis.exceptions import ConnectionError as RedisConnectionError
from redis.exceptions import TimeoutError as RedisTimeoutError

from app.core.settings import Settings

if TYPE_CHECKING:
    from types_aiobotocore_s3 import S3Client


def open_redis(settings: Settings) -> Redis:
    """A pooled client that retries a dropped connection, so a Redis restart is not a 5xx."""
    return Redis.from_url(
        settings.redis_url,
        decode_responses=True,
        retry=Retry(ExponentialBackoff(cap=2.0, base=0.1), retries=8),
        retry_on_error=[RedisConnectionError, RedisTimeoutError],
        health_check_interval=10,
        socket_keepalive=True,
    )


@asynccontextmanager
async def open_s3(settings: Settings) -> AsyncIterator["S3Client"]:
    """An S3 client for SeaweedFS or any S3 API."""
    config = AioConfig(
        s3={"addressing_style": "path"},
        retries={"max_attempts": 3, "mode": "standard"},
        request_checksum_calculation="when_required",
        response_checksum_validation="when_required",
    )
    session = get_session()
    async with session.create_client(
        "s3",
        endpoint_url=settings.s3_endpoint_url,
        region_name=settings.s3_region,
        aws_access_key_id=settings.s3_access_key,
        aws_secret_access_key=settings.s3_secret_key,
        config=config,
    ) as client:
        yield client


@asynccontextmanager
async def open_http(settings: Settings) -> AsyncIterator[httpx.AsyncClient]:
    """The pooled client for OpenRouter."""
    async with httpx.AsyncClient(
        base_url=settings.openrouter_base_url,
        timeout=httpx.Timeout(settings.openrouter_timeout_s, connect=10.0),
        headers={"X-Title": "parse-pdf"},
    ) as client:
        yield client
