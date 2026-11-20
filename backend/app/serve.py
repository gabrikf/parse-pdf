"""API process entry point: validate the configuration, then start uvicorn.

Settings are checked before uvicorn forks its workers, so a missing or short
``SESSION_SECRET`` stops the container at once with a message that names it.
"""

import os
import sys

import uvicorn
from pydantic import ValidationError

from app.core.settings import Settings

API_WORKERS = 2


def describe(error: ValidationError) -> str:
    """Name every invalid variable the way it is written in ``.env``."""
    problems = []
    for item in error.errors():
        name = str(item["loc"][0]).upper() if item["loc"] else "CONFIGURATION"
        problems.append(f"{name}: {item['msg']}")
    return "Invalid configuration - " + "; ".join(problems)


def main() -> int:
    """Return 1 on bad configuration; otherwise serve until stopped."""
    try:
        Settings()
    except ValidationError as exc:
        print(describe(exc), file=sys.stderr)  # noqa: T201 - shown before logging exists
        return 1

    uvicorn.run(
        "app.main:create_app",
        factory=True,
        host="0.0.0.0",  # noqa: S104 - inside the container network, behind nginx
        port=int(os.environ.get("API_PORT", "8000")),
        workers=int(os.environ.get("API_WORKERS", str(API_WORKERS))),
        proxy_headers=True,
        forwarded_allow_ips="*",
        log_level="warning",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
