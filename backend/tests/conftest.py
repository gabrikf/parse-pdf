"""Shared fixtures. Integration tests need `docker compose -f compose.test.yaml up -d --wait`."""

import os
from collections.abc import AsyncIterator

import pytest
from redis.asyncio import Redis

from app.core.settings import Settings

TEST_REDIS_URL = os.environ.get("TEST_REDIS_URL", "redis://127.0.0.1:56379/1")
TEST_S3_URL = os.environ.get("TEST_S3_URL", "http://127.0.0.1:58333")
TEST_SECRET = "test-secret-that-is-at-least-32-bytes-long"


def make_settings(**overrides: object) -> Settings:
    """Settings for tests: real local Redis and SeaweedFS, OpenRouter on a fake host."""
    values: dict[str, object] = {
        "session_secret": TEST_SECRET,
        "redis_url": TEST_REDIS_URL,
        "s3_endpoint_url": TEST_S3_URL,
        "s3_access_key": "test-access",
        "s3_secret_key": "test-secret-key",
        "s3_bucket": "documents-test",
        "page_origin": "http://localhost:8080",
        "openrouter_api_key": "test-key",
        "openrouter_base_url": "https://openrouter.test/api/v1",
        "log_level": "WARNING",
    }
    values.update(overrides)
    return Settings(**values)  # type: ignore[arg-type]


@pytest.fixture
def settings() -> Settings:
    """Default test settings."""
    return make_settings()


@pytest.fixture
async def redis() -> AsyncIterator[Redis]:
    """A clean Redis database; fails loudly when the test Redis is not running."""
    client = Redis.from_url(TEST_REDIS_URL, decode_responses=True)
    try:
        await client.ping()
    except Exception as exc:  # noqa: BLE001
        pytest.fail(f"test Redis not reachable at {TEST_REDIS_URL}: {exc}")
    await client.flushdb()
    yield client
    await client.aclose()
