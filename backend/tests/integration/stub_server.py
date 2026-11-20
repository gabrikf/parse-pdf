"""Run the OpenRouter stub on a free local port in a background thread."""

import socket
import threading
import time
from collections.abc import Iterator
from contextlib import contextmanager

import uvicorn

from stubs.openrouter_stub import app


def _free_port() -> int:
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        port: int = probe.getsockname()[1]
        return port


@contextmanager
def running_stub() -> Iterator[str]:
    """Yield the stub's base URL (``.../api/v1``) while it serves."""
    port = _free_port()
    server = uvicorn.Server(uvicorn.Config(app, host="127.0.0.1", port=port, log_level="error"))
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()
    while not server.started:
        time.sleep(0.02)
    try:
        yield f"http://127.0.0.1:{port}/api/v1"
    finally:
        server.should_exit = True
        thread.join(timeout=5)
