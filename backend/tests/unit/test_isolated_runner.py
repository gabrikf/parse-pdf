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


def _length(data: bytes) -> int:
    return len(data)


async def _longest_gap(work: "asyncio.Future[list[int]]") -> float:
    """The longest the event loop went without running a 1 ms ticker while ``work`` ran."""
    longest = 0.0
    last = time.monotonic()
    while not work.done():
        await asyncio.sleep(0.001)
        now = time.monotonic()
        longest = max(longest, now - last)
        last = now
    await work
    return longest


async def test_starting_children_with_large_pdfs_does_not_block_the_loop() -> None:
    runner = IsolatedRunner(4)
    data = b"%PDF-" + bytes(50 * 1024 * 1024)
    await runner.run(_double, (1,), 30)  # the forkserver is up before the clock starts

    work = asyncio.gather(*(runner.run(_length, (data,), 60) for _ in range(4)))
    gap = await _longest_gap(work)

    assert work.result() == [len(data)] * 4
    assert gap < 0.2
