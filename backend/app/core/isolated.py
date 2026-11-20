"""Run CPU-bound or untrusted work in a child process that can be killed.

PDF inspection and pypdf parsing run here so a hostile file can neither block the event loop
nor hang a worker: each call gets a fresh child from a ``forkserver`` context, a memory cap,
and a deadline after which the child is killed.
"""

import asyncio
import multiprocessing
import resource
from collections.abc import Callable
from multiprocessing.connection import Connection
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


class IsolatedRunner:
    """Bounded pool of one-shot child processes.

    ``max_concurrency`` caps how many children run at once, which also caps the memory the
    copies of the PDF bytes take.
    """

    def __init__(self, max_concurrency: int) -> None:
        self._context = multiprocessing.get_context("forkserver")
        self._slots = asyncio.Semaphore(max_concurrency)

    async def run(self, fn: Callable[..., Any], args: tuple[Any, ...], timeout_s: float) -> Any:
        """Call ``fn(*args)`` in a child and return its result."""
        async with self._slots:
            return await asyncio.to_thread(self._run_blocking, fn, args, timeout_s)

    def _run_blocking(self, fn: Callable[..., Any], args: tuple[Any, ...], timeout_s: float) -> Any:
        receiver, sender = self._context.Pipe(duplex=False)
        child = self._context.Process(target=_child_main, args=(sender, fn, args), daemon=True)
        child.start()
        sender.close()

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
