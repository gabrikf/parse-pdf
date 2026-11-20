"""AD-017: no module under ``backend/app/`` is over 200 lines."""

from pathlib import Path

MAX_LINES = 200
APP = Path(__file__).resolve().parents[2] / "app"


def test_no_app_module_is_over_200_lines() -> None:
    sizes = {path: len(path.read_text().splitlines()) for path in APP.rglob("*.py")}

    assert len(sizes) > 50
    assert {str(path.relative_to(APP)): n for path, n in sizes.items() if n > MAX_LINES} == {}
