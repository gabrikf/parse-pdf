"""Fixtures for tests against the real app."""

from collections.abc import AsyncIterator

import httpx
import pytest
from redis.asyncio import Redis
from types_aiobotocore_s3 import S3Client

from app.core.settings import Settings
from app.infrastructure import open_s3
from tests.integration.harness import open_session, running_app


@pytest.fixture
async def client(settings: Settings, redis: Redis) -> AsyncIterator[httpx.AsyncClient]:
    """A client of a freshly started app over a clean Redis."""
    del redis
    async with running_app(settings) as app_client:
        yield app_client


@pytest.fixture
async def session_client(client: httpx.AsyncClient) -> httpx.AsyncClient:
    """The client, holding a session cookie."""
    await open_session(client)
    return client


@pytest.fixture
async def s3(settings: Settings) -> AsyncIterator[S3Client]:
    """An S3 client on the test bucket's endpoint."""
    async with open_s3(settings) as s3_client:
        yield s3_client
