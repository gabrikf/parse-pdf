"""Criterion 41: the healthcheck fails once the heartbeat is older than 30 s."""

import asyncio
import time
from pathlib import Path

import pytest

from app.worker.heartbeat import beat_forever, is_fresh, main


def test_29s_old_is_fresh_and_31s_old_is_stale(tmp_path: Path) -> None:
    beat = tmp_path / "hb"
    beat.write_text("1000.0")

    assert is_fresh(beat, now=1029.0) is True
    assert is_fresh(beat, now=1031.0) is False


def test_missing_or_garbled_heartbeat_is_stale(tmp_path: Path) -> None:
    garbled = tmp_path / "garbled"
    garbled.write_text("not a time")

    assert is_fresh(tmp_path / "missing", now=time.time()) is False
    assert is_fresh(garbled, now=time.time()) is False


def test_main_exit_codes(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    beat = tmp_path / "hb"
    monkeypatch.setenv("HEARTBEAT_PATH", str(beat))

    beat.write_text(str(time.time()))
    assert main() == 0
    beat.write_text(str(time.time() - 31))
    assert main() == 1


async def test_beat_forever_writes_the_time(tmp_path: Path) -> None:
    beat = tmp_path / "hb"
    task = asyncio.create_task(beat_forever(beat, every_s=0.05))
    await asyncio.sleep(0.12)
    task.cancel()

    assert abs(float(beat.read_text()) - time.time()) < 1
