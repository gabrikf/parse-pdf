"""Criterion 37's message: the 6th delivery's hint names the tries and the last recorded cause."""

from dataclasses import dataclass

import httpx
from redis.asyncio import Redis
from types_aiobotocore_s3 import S3Client

from app.core.settings import Settings
from app.documents.domain.job_errors import TransientFailure
from app.documents.use_cases.process_document import JobOutcome
from app.models.chat_model import ChatRequest
from tests.fakes import FakeChat
from tests.integration.harness import pdf_part, upload
from tests.integration.worker_parts import build_worker
from tests.pdf_factory import make_pdf


@dataclass
class TimingOutChat(FakeChat):
    """Every call ends as if the retries inside one delivery all timed out."""

    async def complete(self, request: ChatRequest) -> str:
        self.calls.append(request)
        raise TransientFailure("timeout")


async def test_a_timed_out_delivery_is_named_when_the_tries_run_out(
    session_client: httpx.AsyncClient, redis: Redis, s3: S3Client, settings: Settings
) -> None:
    response = await upload(session_client, [pdf_part("a.pdf", make_pdf(["alpha"]))])
    document_id = response.json()["data"]["documents"][0]["id"]
    await redis.hset(f"doc:{document_id}", "deliveries", 4)
    parts = build_worker(redis, s3, settings, TimingOutChat())
    await parts.queue.ensure_group()
    job = await parts.queue.read(block_ms=100)
    assert job is not None

    assert await parts.process.execute(job) is JobOutcome.PENDING
    assert await redis.hget(f"doc:{document_id}", "last_error") == "the model provider timed out"

    assert await parts.process.execute(job) is JobOutcome.ACKED
    document = (await session_client.get(f"/api/v1/documents/{document_id}")).json()["data"]
    assert document["status"] == "dead"
    assert document["error_code"] == "max_deliveries"
    assert document["hint"] == (
        "Processing stopped after 5 tries. The last error was: the model provider timed out."
    )
