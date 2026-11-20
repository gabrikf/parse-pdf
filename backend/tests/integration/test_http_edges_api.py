"""Criteria 18 (CORS), 19 (security headers), 20 (500 envelope) and 21 (health)."""

import dataclasses
from collections.abc import AsyncIterator

import httpx
import pytest
from asgi_lifespan import LifespanManager
from fastapi import FastAPI
from redis.asyncio import Redis

from app.container import DependencyProbe
from app.core.settings import Settings
from app.infrastructure import open_s3
from app.main import create_app
from app.storage.s3_object_storage import S3ObjectStorage

BASIC_HEADERS = {
    "cross-origin-opener-policy": "same-origin",
    "cross-origin-resource-policy": "same-origin",
    "strict-transport-security": "max-age=31536000; includeSubDomains",
    "referrer-policy": "no-referrer",
    "x-permitted-cross-domain-policies": "none",
    "x-dns-prefetch-control": "off",
    "x-content-type-options": "nosniff",
    "x-frame-options": "SAMEORIGIN",
    "origin-agent-cluster": "?1",
    "x-download-options": "noopen",
    "x-xss-protection": "0",
}
SECRET_TEXT = "database password is hunter2"


async def _boom() -> None:
    raise RuntimeError(SECRET_TEXT)


@pytest.fixture
async def app_and_client(
    settings: Settings, redis: Redis
) -> AsyncIterator[tuple[FastAPI, httpx.AsyncClient]]:
    del redis
    app = create_app(settings)
    app.add_api_route("/api/v1/boom", _boom)
    async with LifespanManager(app) as manager:
        transport = httpx.ASGITransport(app=manager.app)
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
            yield app, client


async def _responses(client: httpx.AsyncClient) -> dict[int, httpx.Response]:
    await client.post("/api/v1/sessions")
    return {
        200: await client.get("/api/v1/health/live"),
        404: await client.get("/api/v1/documents/00000000-0000-4000-8000-000000000000"),
        422: await client.get("/api/v1/documents", params={"limit": "0"}),
        500: await client.get("/api/v1/boom"),
    }


async def test_basic_preset_headers_on_200_404_422_500(
    app_and_client: tuple[FastAPI, httpx.AsyncClient],
) -> None:
    responses = await _responses(app_and_client[1])

    for status, response in responses.items():
        assert response.status_code == status
        for name, value in BASIC_HEADERS.items():
            assert response.headers.get(name) == value, (status, name)
        assert "content-security-policy" in response.headers


async def test_500_is_an_envelope_without_exception_text(
    app_and_client: tuple[FastAPI, httpx.AsyncClient],
) -> None:
    response = await app_and_client[1].get("/api/v1/boom")

    assert response.status_code == 500
    body = response.json()
    assert body["error"]["code"] == "internal_error"
    assert body["data"] is None
    assert SECRET_TEXT not in response.text
    assert "Traceback" not in response.text
    assert body["meta"]["request_id"] == response.headers["X-Request-ID"]


async def test_unknown_route_is_an_envelope(
    app_and_client: tuple[FastAPI, httpx.AsyncClient],
) -> None:
    response = await app_and_client[1].get("/api/v1/nope")

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "not_found"


async def test_cors_echoes_page_origin_with_credentials(
    app_and_client: tuple[FastAPI, httpx.AsyncClient],
) -> None:
    client = app_and_client[1]
    headers = {"Origin": "http://localhost:8080"}

    simple = await client.get("/api/v1/health/live", headers=headers)
    preflight = await client.options(
        "/api/v1/documents",
        headers={**headers, "Access-Control-Request-Method": "POST"},
    )

    for response in (simple, preflight):
        assert response.headers["access-control-allow-origin"] == "http://localhost:8080"
        assert response.headers["access-control-allow-credentials"] == "true"


@pytest.mark.parametrize("origin", ["http://evil.test", "http://localhost:5173", "null"])
async def test_cors_sends_nothing_for_other_origins(
    app_and_client: tuple[FastAPI, httpx.AsyncClient], origin: str
) -> None:
    client = app_and_client[1]

    simple = await client.get("/api/v1/health/live", headers={"Origin": origin})
    preflight = await client.options(
        "/api/v1/documents",
        headers={"Origin": origin, "Access-Control-Request-Method": "POST"},
    )

    for response in (simple, preflight):
        assert "access-control-allow-origin" not in response.headers
        assert response.headers.get("access-control-allow-origin") != "*"


async def test_ready_is_200_when_redis_and_bucket_answer(
    app_and_client: tuple[FastAPI, httpx.AsyncClient],
) -> None:
    response = await app_and_client[1].get("/api/v1/health/ready")

    assert response.status_code == 200
    assert response.json()["data"] == {
        "status": "ok",
        "checks": {"redis": "ok", "storage": "ok", "openrouter": "ok"},
    }


async def test_ready_is_503_naming_each_failing_check(
    app_and_client: tuple[FastAPI, httpx.AsyncClient], settings: Settings
) -> None:
    app, client = app_and_client
    broken_redis = Redis.from_url("redis://127.0.0.1:1/0", socket_connect_timeout=0.2)
    async with open_s3(settings) as s3:
        probe = DependencyProbe(broken_redis, S3ObjectStorage(s3, "no-such-bucket"), settings)
        original = app.state.services
        app.state.services = dataclasses.replace(original, health=probe)
        try:
            response = await client.get("/api/v1/health/ready")
        finally:
            app.state.services = original
    await broken_redis.aclose()

    assert response.status_code == 503
    body = response.json()
    assert body["error"]["code"] == "not_ready"
    assert body["error"]["details"]["failing"] == ["redis", "storage"]
    assert body["data"]["checks"]["redis"] == "down"


async def test_live_is_200(app_and_client: tuple[FastAPI, httpx.AsyncClient]) -> None:
    response = await app_and_client[1].get("/api/v1/health/live")

    assert response.status_code == 200
    assert response.json()["data"] == {"status": "ok"}
