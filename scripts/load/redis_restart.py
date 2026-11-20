"""Criterion 24's proof against a running stack: Redis restarts with 5 documents queued.

Workers are stopped so the 5 uploads stay ``queued``; Redis restarts (AOF on); the first API
request after Redis is healthy again must not be a 5xx; workers start; all 5 must reach
``ready``. Exit 0 only when that holds.

    .venv/bin/python scripts/load/redis_restart.py --base http://localhost:8081
"""

import argparse
import asyncio
import subprocess
import sys
import time
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parents[2]
SAMPLE = ROOT / "samples" / "w3c-dummy.pdf"
DOCUMENTS = 5
READY_TIMEOUT_S = 180


def report(line: str) -> None:
    """Write one line of the run to stdout."""
    sys.stdout.write(line + "\n")


def compose(project: str, *args: str) -> None:
    """Run one ``docker compose`` command on the project and echo it."""
    report(f"$ docker compose -p {project} {' '.join(args)}")
    subprocess.run(  # noqa: S603 - fixed docker arguments
        ["docker", "compose", "-p", project, *args],  # noqa: S607
        check=True,
        cwd=ROOT,
        capture_output=True,
    )


async def _statuses(client: httpx.AsyncClient, ids: list[str]) -> list[str]:
    reads = [await client.get(f"/api/v1/documents/{document_id}") for document_id in ids]
    return [read.json()["data"]["status"] for read in reads]


async def run(base: str, project: str) -> bool:
    """Queue 5, restart Redis, check the first request, then wait for ``ready``."""
    async with httpx.AsyncClient(base_url=base, timeout=60) as client:
        (await client.post("/api/v1/sessions")).raise_for_status()
        compose(project, "stop", "worker")
        files = [
            ("files", (f"doc-{n}.pdf", SAMPLE.read_bytes(), "application/pdf"))
            for n in range(DOCUMENTS)
        ]
        uploaded = await client.post("/api/v1/documents", files=files, data={"parser": "pypdf"})
        ids = [item["id"] for item in uploaded.json()["data"]["documents"]]
        report(f"uploaded: {uploaded.status_code}, statuses {await _statuses(client, ids)}")

        compose(project, "restart", "redis")
        compose(project, "up", "-d", "--wait", "redis")
        first = await client.get("/api/v1/documents")
        report(f"first request after Redis is back: {first.status_code}")
        report(f"statuses after restart: {await _statuses(client, ids)}")

        compose(project, "start", "worker")
        deadline = time.monotonic() + READY_TIMEOUT_S
        statuses = await _statuses(client, ids)
        while time.monotonic() < deadline and set(statuses) != {"ready"}:
            await asyncio.sleep(1)
            statuses = await _statuses(client, ids)
        report(f"final statuses: {statuses}")

    return (
        uploaded.status_code == 202
        and first.status_code < 500
        and statuses == ["ready"] * DOCUMENTS
    )


def main() -> int:
    """Parse the arguments, run, and print the verdict."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", default="http://localhost:8081")
    parser.add_argument("--project", default="parse-pdf-e2e")
    args = parser.parse_args()
    passed = asyncio.run(run(args.base, args.project))
    report(f"result: {'PASSED' if passed else 'FAILED'}")
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
