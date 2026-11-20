"""Criteria 13-16 and 20: the feed, one document, its pages, and ownership."""

import httpx
import pytest
from redis.asyncio import Redis

from app.documents.domain.document_status import DocumentStatus
from tests.integration.harness import bearer, open_session
from tests.integration.seed import seed

UNKNOWN_ID = "00000000-0000-4000-8000-000000000000"


async def _session_id(client: httpx.AsyncClient) -> str:
    response = await client.post("/api/v1/sessions")
    return str(response.json()["data"]["session_id"])


async def test_feed_pages_newest_first_with_cursor(
    session_client: httpx.AsyncClient, redis: Redis
) -> None:
    sid = await _session_id(session_client)
    created = [await seed(redis, sid, i, DocumentStatus.QUEUED) for i in range(45)]
    newest_first = [d.id for d in reversed(created)]

    seen: list[str] = []
    cursors: list[str | None] = []
    params: dict[str, str] = {"limit": "20"}
    for _ in range(3):
        body = (await session_client.get("/api/v1/documents", params=params)).json()
        seen += [d["id"] for d in body["data"]]
        cursors.append(body["meta"]["next_cursor"])
        params["cursor"] = body["meta"]["next_cursor"] or ""

    assert seen == newest_first
    assert cursors[0] is not None
    assert cursors[1] is not None
    assert cursors[2] is None


async def test_feed_default_limit_is_20(session_client: httpx.AsyncClient, redis: Redis) -> None:
    sid = await _session_id(session_client)
    for i in range(25):
        await seed(redis, sid, i, DocumentStatus.QUEUED)

    body = (await session_client.get("/api/v1/documents")).json()

    assert len(body["data"]) == 20
    assert body["meta"]["limit"] == 20


@pytest.mark.parametrize("limit", ["0", "51", "abc", "", "-1"])
async def test_bad_limit_is_422(session_client: httpx.AsyncClient, limit: str) -> None:
    response = await session_client.get("/api/v1/documents", params={"limit": limit})

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "invalid_limit"


async def test_limit_50_is_accepted(session_client: httpx.AsyncClient) -> None:
    response = await session_client.get("/api/v1/documents", params={"limit": "50"})

    assert response.status_code == 200


async def test_bad_cursor_is_422(session_client: httpx.AsyncClient) -> None:
    response = await session_client.get("/api/v1/documents", params={"cursor": "%%%not-ours"})

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "invalid_cursor"


async def test_feed_states_filter_groups_and_count(
    session_client: httpx.AsyncClient, redis: Redis
) -> None:
    sid = await _session_id(session_client)
    queued = await seed(redis, sid, 0, DocumentStatus.QUEUED)
    ready = [await seed(redis, sid, i, DocumentStatus.READY) for i in (1, 2)]
    dead = await seed(redis, sid, 3, DocumentStatus.DEAD)

    async def ids(state: str | None) -> list[str]:
        params = {"state": state} if state is not None else {}
        body = (await session_client.get("/api/v1/documents", params=params)).json()
        return [d["id"] for d in body["data"]]

    assert await ids("parsed") == [ready[1].id, ready[0].id]
    assert await ids("failed") == [dead.id]
    assert await ids("active") == [queued.id]
    assert len(await ids(None)) == 4
    assert len(await ids("all")) == 4
    meta = (await session_client.get("/api/v1/documents")).json()["meta"]
    assert meta["counts"] == {"parsed": 2, "failed": 1, "active": 1, "all": 4}


async def test_feed_parsed_holds_no_text_and_failed_holds_too_large(
    session_client: httpx.AsyncClient, redis: Redis
) -> None:
    sid = await _session_id(session_client)
    no_text = await seed(redis, sid, 0, DocumentStatus.NO_TEXT)
    too_large = await seed(redis, sid, 1, DocumentStatus.TOO_LARGE)
    processing = await seed(redis, sid, 2, DocumentStatus.PROCESSING)

    def ids(body: dict[str, list[dict[str, str]]]) -> list[str]:
        return [d["id"] for d in body["data"]]

    get = session_client.get
    assert ids((await get("/api/v1/documents?state=parsed")).json()) == [no_text.id]
    assert ids((await get("/api/v1/documents?state=failed")).json()) == [too_large.id]
    assert ids((await get("/api/v1/documents?state=active")).json()) == [processing.id]


@pytest.mark.parametrize("state", ["", "final", "PARSED"])
async def test_unknown_state_is_422(session_client: httpx.AsyncClient, state: str) -> None:
    response = await session_client.get("/api/v1/documents", params={"state": state})

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "invalid_state"


async def test_feed_shows_only_own_documents(client: httpx.AsyncClient, redis: Redis) -> None:
    mine_token = await open_session(client)
    client.cookies.clear()
    theirs_token = await open_session(client)
    client.cookies.clear()
    mine = (await client.post("/api/v1/sessions", headers=bearer(mine_token))).json()
    theirs = (await client.post("/api/v1/sessions", headers=bearer(theirs_token))).json()
    await seed(redis, mine["data"]["session_id"], 0, DocumentStatus.READY)
    await seed(redis, theirs["data"]["session_id"], 1, DocumentStatus.READY)

    body = (await client.get("/api/v1/documents", headers=bearer(mine_token))).json()

    assert len(body["data"]) == 1
    assert body["data"][0]["filename"] == "doc-0.pdf"


@pytest.mark.parametrize(
    ("method", "suffix", "body"),
    [
        ("GET", "", None),
        ("GET", "/pages", None),
        ("POST", "/reparse", {"parser": "pypdf"}),
        ("POST", "/requeue", None),
        ("DELETE", "", None),
    ],
    ids=["read", "pages", "reparse", "requeue", "delete"],
)
async def test_foreign_document_is_404_like_a_missing_one(
    client: httpx.AsyncClient,
    redis: Redis,
    method: str,
    suffix: str,
    body: dict[str, str] | None,
) -> None:
    owner = await open_session(client)
    client.cookies.clear()
    stranger = await open_session(client)
    client.cookies.clear()
    owner_sid = (await client.post("/api/v1/sessions", headers=bearer(owner))).json()
    document = await seed(redis, owner_sid["data"]["session_id"], 0, DocumentStatus.DEAD)

    foreign = await client.request(
        method, f"/api/v1/documents/{document.id}{suffix}", json=body, headers=bearer(stranger)
    )
    missing = await client.request(
        method, f"/api/v1/documents/{UNKNOWN_ID}{suffix}", json=body, headers=bearer(stranger)
    )

    assert foreign.status_code == missing.status_code == 404
    assert foreign.json()["error"] == missing.json()["error"]
    assert foreign.json()["error"]["code"] == "document_not_found"
    assert await redis.exists(f"doc:{document.id}") == 1


@pytest.mark.parametrize(
    "status",
    [
        DocumentStatus.QUEUED,
        DocumentStatus.PROCESSING,
        DocumentStatus.NO_TEXT,
        DocumentStatus.TOO_LARGE,
        DocumentStatus.DEAD,
    ],
)
async def test_not_ready_document_hides_summary_and_pages(
    session_client: httpx.AsyncClient, redis: Redis, status: DocumentStatus
) -> None:
    sid = await _session_id(session_client)
    document = await seed(redis, sid, 0, status)

    read = await session_client.get(f"/api/v1/documents/{document.id}")
    pages = await session_client.get(f"/api/v1/documents/{document.id}/pages")

    assert read.json()["data"]["summary"] is None
    assert pages.status_code == 409
    assert pages.json()["error"]["code"] == "not_ready"


async def test_ready_document_shows_summary_and_pages_in_order(
    session_client: httpx.AsyncClient, redis: Redis
) -> None:
    sid = await _session_id(session_client)
    texts = [f"text {n}" for n in range(1, 121)]
    document = await seed(redis, sid, 0, DocumentStatus.READY, pages=texts, summary="# Sum")

    read = (await session_client.get(f"/api/v1/documents/{document.id}")).json()
    first = (await session_client.get(f"/api/v1/documents/{document.id}/pages")).json()
    rest = (
        await session_client.get(
            f"/api/v1/documents/{document.id}/pages", params={"offset": "100", "limit": "100"}
        )
    ).json()

    assert read["data"]["summary"] == "# Sum"
    assert [p["number"] for p in first["data"]] == list(range(1, 51))
    assert first["data"][0] == {"number": 1, "content": "text 1", "format": "text"}
    assert first["meta"]["total"] == 120
    assert [p["number"] for p in rest["data"]] == list(range(101, 121))


@pytest.mark.parametrize("limit", ["0", "101", "x"])
async def test_bad_pages_limit_is_422(
    session_client: httpx.AsyncClient, redis: Redis, limit: str
) -> None:
    sid = await _session_id(session_client)
    document = await seed(redis, sid, 0, DocumentStatus.READY)

    response = await session_client.get(
        f"/api/v1/documents/{document.id}/pages", params={"limit": limit}
    )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "invalid_limit"


async def test_envelope_and_request_id_on_success_and_error(
    session_client: httpx.AsyncClient,
) -> None:
    ok = await session_client.get("/api/v1/documents")
    missing = await session_client.get(f"/api/v1/documents/{UNKNOWN_ID}")

    for response in (ok, missing):
        body = response.json()
        assert set(body) == {"data", "error", "meta"}
        assert body["meta"]["request_id"] == response.headers["X-Request-ID"]
    assert ok.json()["error"] is None
    assert missing.json()["data"] is None
