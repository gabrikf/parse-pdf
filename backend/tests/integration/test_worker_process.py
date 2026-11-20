"""Criteria 35, 40 and 41 against real worker processes (``python -m app.worker.main``)."""

import asyncio
import os
import signal
import subprocess
import sys
from collections.abc import Iterator
from pathlib import Path

import httpx
import pytest
from redis.asyncio import Redis

from app.core.settings import Settings
from tests.conftest import TEST_REDIS_URL, TEST_S3_URL, TEST_SECRET
from tests.integration.harness import pdf_part, upload
from tests.integration.stub_server import running_stub
from tests.pdf_factory import make_pdf

BACKEND = Path(__file__).resolve().parents[2]


@pytest.fixture
def stub_url() -> Iterator[str]:
    with running_stub() as url:
        yield url


def _start_worker(stub_url: str, settings: Settings, heartbeat: Path) -> subprocess.Popen[bytes]:
    env = {
        **os.environ,
        "SESSION_SECRET": TEST_SECRET,
        "REDIS_URL": TEST_REDIS_URL,
        "S3_ENDPOINT_URL": TEST_S3_URL,
        "S3_ACCESS_KEY": settings.s3_access_key,
        "S3_SECRET_KEY": settings.s3_secret_key,
        "S3_BUCKET": settings.s3_bucket,
        "OPENROUTER_API_KEY": "stub-key",
        "OPENROUTER_BASE_URL": stub_url,
        "JOB_CLAIM_IDLE_MS": "1500",
        "RECLAIM_SWEEP_S": "0.3",
        "CLAIM_REFRESH_S": "0.5",
        "HEARTBEAT_PATH": str(heartbeat),
        "HEARTBEAT_INTERVAL_S": "0.5",
        "LOG_LEVEL": "WARNING",
    }
    return subprocess.Popen([sys.executable, "-m", "app.worker.main"], cwd=BACKEND, env=env)


async def _wait_status(redis: Redis, document_id: str, wanted: str, seconds: float) -> str:
    status = ""
    for _ in range(int(seconds / 0.1)):
        status = str(await redis.hget(f"doc:{document_id}", "status") or "")
        if status == wanted:
            break
        await asyncio.sleep(0.1)
    return status


async def test_sigkilled_worker_job_is_reclaimed_and_ends_ready(
    session_client: httpx.AsyncClient,
    redis: Redis,
    settings: Settings,
    stub_url: str,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("STUB_DELAY_S", "30")
    response = await upload(session_client, [pdf_part("a.pdf", make_pdf(["alpha"]))])
    document_id = response.json()["data"]["documents"][0]["id"]

    first = _start_worker(stub_url, settings, tmp_path / "hb1")
    try:
        assert await _wait_status(redis, document_id, "processing", 20) == "processing"
        first.send_signal(signal.SIGKILL)
        first.wait(timeout=10)
    finally:
        first.kill()

    monkeypatch.setenv("STUB_DELAY_S", "0")
    second = _start_worker(stub_url, settings, tmp_path / "hb2")
    try:
        assert await _wait_status(redis, document_id, "ready", 30) == "ready"
    finally:
        second.terminate()
        second.wait(timeout=40)

    assert await redis.hget(f"doc:{document_id}", "deliveries") == "2"


async def test_sigterm_exits_cleanly_and_heartbeat_goes_stale(
    redis: Redis, settings: Settings, stub_url: str, tmp_path: Path
) -> None:
    del redis
    heartbeat = tmp_path / "hb"
    worker = _start_worker(stub_url, settings, heartbeat)
    try:
        for _ in range(100):
            if heartbeat.exists():
                break
            await asyncio.sleep(0.1)
        fresh = await asyncio.to_thread(
            subprocess.run,
            [sys.executable, "-m", "app.worker.heartbeat"],
            cwd=BACKEND,
            env={**os.environ, "HEARTBEAT_PATH": str(heartbeat)},
            check=False,
        )
        worker.send_signal(signal.SIGTERM)
        code = await asyncio.to_thread(worker.wait, 35)
    finally:
        worker.kill()

    assert fresh.returncode == 0
    assert code == 0
