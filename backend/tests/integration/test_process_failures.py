"""Criteria 27, 31, 32 and 33 at the worker: summary before ready, guardrail, provider errors."""

from dataclasses import dataclass, field

import httpx
import pytest
from redis.asyncio import Redis
from types_aiobotocore_s3 import S3Client

from app.core.settings import Settings
from app.documents.domain.job_errors import PermanentFailure, TransientFailure
from app.documents.use_cases.process_document import JobOutcome
from app.models.chat_model import ChatModel, ChatRequest
from app.queue.job import CONSUMER_GROUP, DEAD_LETTER_KEY, STREAM_KEY
from tests.fakes import GUARD_MODEL, FakeChat
from tests.integration.harness import pdf_part, upload
from tests.integration.worker_parts import build_worker
from tests.pdf_factory import make_pdf


@dataclass
class FailingChat:
    """Guard calls pass; every other call raises ``failure``."""

    failure: Exception
    calls: list[ChatRequest] = field(default_factory=list)

    async def complete(self, request: ChatRequest) -> str:
        self.calls.append(request)
        if request.model == GUARD_MODEL:
            return "safe"
        raise self.failure


async def _upload(client: httpx.AsyncClient) -> str:
    response = await upload(client, [pdf_part("a.pdf", make_pdf(["alpha text"]))])
    assert response.status_code == 202, response.text
    document_id: str = response.json()["data"]["documents"][0]["id"]
    return document_id


async def _deliver(redis: Redis, s3: S3Client, settings: Settings, chat: ChatModel) -> JobOutcome:
    parts = build_worker(redis, s3, settings, chat)
    await parts.queue.ensure_group()
    job = await parts.queue.read(block_ms=100) or await parts.queue.reclaim(0)
    assert job is not None
    return await parts.process.execute(job)


async def test_ready_is_set_only_with_the_stored_summary(
    session_client: httpx.AsyncClient, redis: Redis, s3: S3Client, settings: Settings
) -> None:
    document_id = await _upload(session_client)
    chat = FakeChat(reply="## Overview\nStored summary.")

    await _deliver(redis, s3, settings, chat)

    read = (await session_client.get(f"/api/v1/documents/{document_id}")).json()["data"]
    assert read["status"] == "ready"
    assert read["summary"] == "## Overview\nStored summary."
    assert [call.model for call in chat.calls if call.model != GUARD_MODEL] == [
        "google/gemini-3.1-flash-lite"
    ]


@pytest.mark.parametrize(
    "code", ["provider_rejected", "provider_out_of_credits", "provider_not_configured"]
)
async def test_permanent_provider_errors_end_dead_without_retry(
    session_client: httpx.AsyncClient,
    redis: Redis,
    s3: S3Client,
    settings: Settings,
    code: str,
) -> None:
    document_id = await _upload(session_client)
    chat = FailingChat(PermanentFailure(code))

    outcome = await _deliver(redis, s3, settings, chat)

    assert outcome is JobOutcome.ACKED
    record = await redis.hgetall(f"doc:{document_id}")
    assert (record["status"], record["error_code"]) == ("dead", code)
    assert len([call for call in chat.calls if call.model != GUARD_MODEL]) == 1
    assert await redis.xlen(DEAD_LETTER_KEY) == 1
    assert await redis.xlen(STREAM_KEY) == 0


async def test_retries_run_out_and_the_entry_stays_pending_for_redelivery(
    session_client: httpx.AsyncClient, redis: Redis, s3: S3Client, settings: Settings
) -> None:
    document_id = await _upload(session_client)

    outcome = await _deliver(redis, s3, settings, FailingChat(TransientFailure("6 x 429")))

    assert outcome is JobOutcome.PENDING
    assert await redis.hget(f"doc:{document_id}", "status") == "processing"
    pending = await redis.xpending(STREAM_KEY, CONSUMER_GROUP)
    assert pending["pending"] == 1

    again = await _deliver(redis, s3, settings, FakeChat())

    assert again is JobOutcome.ACKED
    record = await redis.hgetall(f"doc:{document_id}")
    assert (record["status"], record["deliveries"]) == ("ready", "2")


@pytest.mark.parametrize("verdict", ["unsafe\nS1", "unsafe"])
async def test_unsafe_input_ends_dead_guardrail_rejected_without_a_summary_call(
    session_client: httpx.AsyncClient,
    redis: Redis,
    s3: S3Client,
    settings: Settings,
    verdict: str,
) -> None:
    document_id = await _upload(session_client)
    chat = FakeChat(guard_verdict=verdict)

    await _deliver(redis, s3, settings, chat)

    record = await redis.hgetall(f"doc:{document_id}")
    assert (record["status"], record["error_code"]) == ("dead", "guardrail_rejected")
    assert [call.model for call in chat.calls] == [GUARD_MODEL]
