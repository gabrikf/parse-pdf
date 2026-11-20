"""Run the real app (real Redis and SeaweedFS) in-process behind an httpx client."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

import httpx
from asgi_lifespan import LifespanManager

from app.core.settings import Settings
from app.main import create_app


@asynccontextmanager
async def running_app(settings: Settings) -> AsyncIterator[httpx.AsyncClient]:
    """Yield a client bound to a started app."""
    app = create_app(settings)
    async with LifespanManager(app) as manager:
        transport = httpx.ASGITransport(app=manager.app)
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
            yield client


async def open_session(client: httpx.AsyncClient) -> str:
    """Create a session; the client keeps the cookie. Returns the token."""
    response = await client.post("/api/v1/sessions")
    assert response.status_code == 201, response.text
    token: str = response.json()["data"]["token"]
    return token


def bearer(token: str) -> dict[str, str]:
    """Authorization header for a token."""
    return {"Authorization": f"Bearer {token}"}


def pdf_part(name: str, data: bytes) -> tuple[str, tuple[str, bytes, str]]:
    """One ``files`` part of a multipart upload."""
    return ("files", (name, data, "application/pdf"))


async def upload(
    client: httpx.AsyncClient,
    files: list[tuple[str, tuple[str, bytes, str]]],
    parser: str | None = "pypdf",
    **extra: Any,
) -> httpx.Response:
    """POST an upload with the given parts."""
    data: dict[str, str] = {} if parser is None else {"parser": parser}
    data.update(extra)
    return await client.post("/api/v1/documents", files=files, data=data)
