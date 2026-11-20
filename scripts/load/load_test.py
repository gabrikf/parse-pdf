"""Criterion 22's load proof against a running stack (``docker compose ... --scale worker=3``).

Phase 1: 5,000 ``GET /api/v1/documents`` at concurrency 200 from one session; every answer must
be 200. Phase 2: 50 sessions upload one PDF each at the same moment; every upload must be 202,
every document must reach ``ready``, and each must have been delivered exactly once
(``deliveries`` read from Redis inside the Compose project). Exit 0 only when both hold.

    .venv/bin/python scripts/load/load_test.py --base http://localhost:8081 --project parse-pdf-e2e
"""

import argparse
import asyncio
import statistics
import subprocess
import sys
import time
from collections import Counter
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parents[2]
SAMPLE = ROOT / "samples" / "w3c-dummy.pdf"
READY_TIMEOUT_S = 300


def report(line: str) -> None:
    """Write one line of the tally to stdout."""
    sys.stdout.write(line + "\n")


def _percentile(values: list[float], share: float) -> float:
    ordered = sorted(values)
    return ordered[min(len(ordered) - 1, int(len(ordered) * share))]


async def _session(client: httpx.AsyncClient) -> None:
    response = await client.post("/api/v1/sessions")
    response.raise_for_status()


async def read_load(base: str, total: int, concurrency: int) -> bool:
    """Fire ``total`` feed reads, ``concurrency`` at a time, and print the tally."""
    limits = httpx.Limits(max_connections=concurrency, max_keepalive_connections=concurrency)
    async with httpx.AsyncClient(base_url=base, limits=limits, timeout=60) as client:
        await _session(client)
        gate = asyncio.Semaphore(concurrency)
        latencies: list[float] = []
        statuses: Counter[int | str] = Counter()

        async def one() -> None:
            async with gate:
                started = time.perf_counter()
                try:
                    response = await client.get("/api/v1/documents")
                    statuses[response.status_code] += 1
                except httpx.HTTPError as error:
                    statuses[type(error).__name__] += 1
                latencies.append(time.perf_counter() - started)

        started = time.perf_counter()
        await asyncio.gather(*(one() for _ in range(total)))
        elapsed = time.perf_counter() - started

    report(f"phase 1: {total} GET /api/v1/documents at concurrency {concurrency}")
    report(f"  statuses: {dict(statuses)}")
    report(f"  elapsed: {elapsed:.2f} s, {total / elapsed:.0f} requests/s")
    report(
        f"  latency ms: p50 {statistics.median(latencies) * 1000:.0f}, "
        f"p95 {_percentile(latencies, 0.95) * 1000:.0f}, "
        f"p99 {_percentile(latencies, 0.99) * 1000:.0f}, max {max(latencies) * 1000:.0f}"
    )
    return statuses == Counter({200: total})


async def _upload_one(base: str, pdf: bytes, start: asyncio.Event) -> tuple[int, str]:
    client = httpx.AsyncClient(base_url=base, timeout=120)
    await _session(client)
    await start.wait()
    response = await client.post(
        "/api/v1/documents",
        files=[("files", ("sample.pdf", pdf, "application/pdf"))],
        data={"parser": "pypdf"},
    )
    document_id = ""
    if response.status_code == 202:
        document_id = response.json()["data"]["documents"][0]["id"]
    status = await _wait_ready(client, document_id) if document_id else "not uploaded"
    await client.aclose()
    return response.status_code, f"{document_id}:{status}"


async def _wait_ready(client: httpx.AsyncClient, document_id: str) -> str:
    deadline = time.monotonic() + READY_TIMEOUT_S
    status = "queued"
    while time.monotonic() < deadline and status in {"queued", "processing"}:
        await asyncio.sleep(0.5)
        status = (await client.get(f"/api/v1/documents/{document_id}")).json()["data"]["status"]
    return status


def _deliveries(project: str, document_ids: list[str]) -> list[str]:
    script = "".join(f"HGET doc:{document_id} deliveries\n" for document_id in document_ids)
    result = subprocess.run(  # noqa: S603 - fixed docker arguments
        ["docker", "compose", "-p", project, "exec", "-T", "redis", "redis-cli"],  # noqa: S607
        input=script,
        capture_output=True,
        text=True,
        check=True,
        cwd=ROOT,
    )
    return result.stdout.split()


async def upload_burst(base: str, project: str, sessions: int) -> bool:
    """``sessions`` sessions upload one PDF each at the same moment."""
    pdf = SAMPLE.read_bytes()
    start = asyncio.Event()
    tasks = [asyncio.create_task(_upload_one(base, pdf, start)) for _ in range(sessions)]
    await asyncio.sleep(2)
    started = time.perf_counter()
    start.set()
    results = await asyncio.gather(*tasks)
    elapsed = time.perf_counter() - started

    codes = Counter(code for code, _ in results)
    finals = Counter(outcome.split(":")[1] for _, outcome in results)
    ids = [outcome.split(":")[0] for _, outcome in results if outcome.split(":")[0]]
    deliveries = Counter(_deliveries(project, ids)) if ids else Counter()
    report(f"phase 2: {sessions} sessions upload one PDF each at the same moment")
    report(f"  upload statuses: {dict(codes)}")
    report(f"  final statuses: {dict(finals)}")
    report(f"  deliveries per document: {dict(deliveries)}")
    report(f"  all ready after {elapsed:.2f} s")
    return (
        codes == Counter({202: sessions})
        and finals == Counter({"ready": sessions})
        and deliveries == Counter({"1": sessions})
    )


async def main() -> int:
    """Run both phases and exit 0 only when both pass."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", default="http://localhost:8081")
    parser.add_argument("--project", default="parse-pdf-e2e")
    parser.add_argument("--reads", type=int, default=5000)
    parser.add_argument("--concurrency", type=int, default=200)
    parser.add_argument("--sessions", type=int, default=50)
    args = parser.parse_args()

    reads_ok = await read_load(args.base, args.reads, args.concurrency)
    uploads_ok = await upload_burst(args.base, args.project, args.sessions)
    passed = reads_ok and uploads_ok
    report(f"result: {'PASSED' if passed else 'FAILED'}")
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
