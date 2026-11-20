"""The runtime image installs no dev or stub packages: entry points must import without them."""

import subprocess
import sys

DEV_ONLY = ["types_aiobotocore_s3", "respx", "pytest", "asgi_lifespan", "mypy", "importlinter"]


def test_entry_points_import_without_dev_packages() -> None:
    block = "; ".join(f"sys.modules[{name!r}] = None" for name in DEV_ONLY)
    code = f"import sys; {block}; import app.main, app.serve, app.worker.main, app.worker.heartbeat"

    result = subprocess.run(  # noqa: S603 - fixed arguments
        [sys.executable, "-c", code], capture_output=True, text=True, check=False
    )

    assert result.returncode == 0, result.stderr
