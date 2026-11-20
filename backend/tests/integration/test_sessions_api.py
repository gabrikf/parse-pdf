"""Criterion 3 (sessions), 4 (session required) and the session part of 17."""

import time

import httpx
import jwt
import pytest

from tests.conftest import TEST_SECRET
from tests.integration.harness import bearer

DOCUMENT_ROUTES = [
    ("GET", "/api/v1/documents"),
    ("POST", "/api/v1/documents"),
    ("GET", "/api/v1/documents/00000000-0000-4000-8000-000000000000"),
    ("GET", "/api/v1/documents/00000000-0000-4000-8000-000000000000/pages"),
    ("POST", "/api/v1/documents/00000000-0000-4000-8000-000000000000/reparse"),
    ("POST", "/api/v1/documents/00000000-0000-4000-8000-000000000000/requeue"),
    ("DELETE", "/api/v1/documents/00000000-0000-4000-8000-000000000000"),
]


async def test_new_session_sets_cookie_and_reuse_returns_same_id(
    client: httpx.AsyncClient,
) -> None:
    first = await client.post("/api/v1/sessions")

    assert first.status_code == 201
    cookie = first.headers["set-cookie"]
    assert cookie.startswith("pp_session=")
    assert "HttpOnly" in cookie
    assert "SameSite=lax" in cookie
    assert "Max-Age=604800" in cookie
    session_id = first.json()["data"]["session_id"]

    second = await client.post("/api/v1/sessions")
    assert second.status_code == 200
    assert second.json()["data"]["session_id"] == session_id


def _token(**claims: object) -> str:
    now = int(time.time())
    payload = {"sub": "11111111-1111-4111-8111-111111111111", "iat": now, "exp": now + 60}
    payload.update(claims)
    return jwt.encode(payload, TEST_SECRET, algorithm="HS256")


@pytest.mark.parametrize(("method", "path"), DOCUMENT_ROUTES)
async def test_document_routes_without_session_are_401(
    client: httpx.AsyncClient, method: str, path: str
) -> None:
    response = await client.request(method, path)

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "session_required"


@pytest.mark.parametrize(
    "token",
    [
        pytest.param(_token()[:-3] + "abc", id="signature tampered"),
        pytest.param(
            jwt.encode({"sub": "11111111-1111-4111-8111-111111111111"}, "", algorithm="none"),
            id="alg none",
        ),
        pytest.param(_token(exp=int(time.time()) - 1), id="expired 1 s ago"),
        pytest.param(
            jwt.encode({"sub": "x"}, "another-secret-of-32-bytes-or-more!!"), id="foreign key"
        ),
    ],
)
async def test_invalid_tokens_are_401(client: httpx.AsyncClient, token: str) -> None:
    response = await client.get("/api/v1/documents", headers=bearer(token))

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "session_required"


async def test_valid_bearer_is_accepted(client: httpx.AsyncClient) -> None:
    response = await client.get("/api/v1/documents", headers=bearer(_token()))

    assert response.status_code == 200


async def test_21st_session_from_one_ip_within_60s_is_429(client: httpx.AsyncClient) -> None:
    for _ in range(20):
        client.cookies.clear()
        assert (await client.post("/api/v1/sessions")).status_code == 201

    client.cookies.clear()
    response = await client.post("/api/v1/sessions")

    assert response.status_code == 429
    assert response.json()["error"]["code"] == "rate_limited"
    assert response.headers["Retry-After"].isdigit()
