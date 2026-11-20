"""Turn SIGTERM and SIGINT into an event the consumer loop watches (criterion 40)."""

import asyncio
import signal


def install_stop_signals(stop: asyncio.Event) -> None:
    """Set ``stop`` on SIGTERM or SIGINT."""
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGTERM, signal.SIGINT):
        loop.add_signal_handler(sig, stop.set)
