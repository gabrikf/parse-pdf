"""Run CPU-bound or untrusted work in a child process that can be killed.

PDF inspection and pypdf parsing run here so a hostile file can neither block the event loop
nor hang a worker: each call gets a fresh child from a ``forkserver`` context, a memory cap,
and a deadline after which the child is killed.
"""

import asyncio
import multiprocessing
import resource
import threading
from collections.abc import Callable
from multiprocessing.connection import Connection
from multiprocessing.process import BaseProcess
from typing import Any

CHILD_MEMORY_BYTES = 1536 * 1024 * 1024


class IsolatedTimeoutError(Exception):
    """The child did not answer before its deadline and was killed."""


class IsolatedCrashError(Exception):
    """The child raised, ran out of memory, or died without an answer."""


def _child_main(conn: Connection, fn: Callable[..., Any], args: tuple[Any, ...]) -> None:
    resource.setrlimit(resource.RLIMIT_AS, (CHILD_MEMORY_BYTES, CHILD_MEMORY_BYTES))
    try:
        conn.send((True, fn(*args)))
    except BaseException as exc:  # noqa: BLE001 - every failure must reach the parent
        conn.send((False, type(exc).__name__))
    finally:
        conn.close()


class _Child:
    """One child: started and waited on in a worker thread, killable from the loop at any time.

    Starting a ``forkserver`` child pickles its arguments (a whole PDF) into a pipe, so the start
    runs in the thread too, never on the event loop.
    """

    def __init__(self, context: Any, fn: Callable[..., Any], args: tuple[Any, ...]) -> None:
        self._context = context
        self._fn = fn
        self._args = args
        self._process: BaseProcess | None = None
        self._killed = threading.Event()

    def run(self, timeout_s: float) -> Any:
        """Start the child, wait for its answer, and return it (worker thread)."""
        receiver, sender = self._context.Pipe(duplex=False)
        process = self._context.Process(
            target=_child_main, args=(sender, self._fn, self._args), daemon=True
        )
        process.start()
        sender.close()

        # Publish the process, then look for a kill that came first: either this check or
        # ``kill`` sees the other, so a cancelled call never leaves its child running.
        self._process = process
        if self._killed.is_set():
            process.kill()
        return _wait(receiver, process, timeout_s)

    def kill(self) -> None:
        """Kill the child now, or as soon as it has started."""
        self._killed.set()
        if self._process is not None:
            self._process.kill()


def _wait(receiver: Connection, child: BaseProcess, timeout_s: float) -> Any:
    try:
        if not receiver.poll(timeout_s):
            child.kill()
            raise IsolatedTimeoutError(f"no answer within {timeout_s} s")
        ok, payload = receiver.recv()
    except EOFError as exc:
        raise IsolatedCrashError("child exited without an answer") from exc
    finally:
        receiver.close()
        child.join(timeout=5)

    if not ok:
        raise IsolatedCrashError(str(payload))
    return payload


class IsolatedRunner:
    """Bounded pool of one-shot child processes.

    ``max_concurrency`` caps how many children run at once, which also caps the memory the
    copies of the PDF bytes take.
    """

    def __init__(self, max_concurrency: int) -> None:
        self._context = multiprocessing.get_context("forkserver")
        self._slots = asyncio.Semaphore(max_concurrency)

    async def run(self, fn: Callable[..., Any], args: tuple[Any, ...], timeout_s: float) -> Any:
        """Call ``fn(*args)`` in a child and return its result.

        A cancelled call kills its child at once, so the slot is never freed while the child
        still holds its memory, and the waiting thread wakes on the closed pipe.
        """
        async with self._slots:
            child = _Child(self._context, fn, args)
            try:
                return await asyncio.to_thread(child.run, timeout_s)
            except asyncio.CancelledError:
                child.kill()
                raise
