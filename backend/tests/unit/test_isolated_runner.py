"""The child-process sandbox: answers, deadline kill, crash."""

import asyncio
import contextlib
import multiprocessing
import time

import pytest

from app.core.isolated import IsolatedCrashError, IsolatedRunner, IsolatedTimeoutError


def _double(value: int) -> int:
    return value * 2


def _hang() -> None:
    time.sleep(30)


def _explode() -> None:
    raise ValueError("boom")


async def test_returns_the_childs_result() -> None:
    assert await IsolatedRunner(2).run(_double, (21,), 10) == 42


async def test_kills_a_child_past_its_deadline() -> None:
    started = time.monotonic()

    with pytest.raises(IsolatedTimeoutError):
        await IsolatedRunner(1).run(_hang, (), 0.5)
    assert time.monotonic() - started < 5


async def test_reports_a_child_that_raises() -> None:
    with pytest.raises(IsolatedCrashError, match="ValueError"):
        await IsolatedRunner(1).run(_explode, (), 10)


async def test_a_cancelled_call_kills_its_child_and_frees_the_slot() -> None:
    runner = IsolatedRunner(1)
    task = asyncio.create_task(runner.run(_hang, (), 60))
    await asyncio.sleep(0.5)
    started = time.monotonic()

    task.cancel()
    with contextlib.suppress(asyncio.CancelledError):
        await task

    for _ in range(50):
        if not multiprocessing.active_children():
            break
        await asyncio.sleep(0.1)
    assert multiprocessing.active_children() == []
    assert await runner.run(_double, (2,), 10) == 4
    assert time.monotonic() - started < 10
