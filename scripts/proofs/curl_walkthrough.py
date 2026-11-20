"""Run the README's curl walkthrough line by line and check each status it shows (criterion 78).

    python3 scripts/proofs/curl_walkthrough.py <base-url>

The block between ``<!-- walkthrough:start -->`` and ``<!-- walkthrough:end -->`` runs in one
bash session from the repository root, with ``BASE`` pointed at ``<base-url>/api/v1`` and the
cookie jar in a temporary folder. A command followed by a ``# NNN`` line must print NNN last.
Only the command, the status and the body's ``data.status`` or ``error.code`` are printed: the
session body holds a token, which never goes to the log.
"""

import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BLOCK = re.compile(
    r"<!-- walkthrough:start -->\n```bash\n(.*?)```\n<!-- walkthrough:end -->", re.DOTALL
)
STATUS = re.compile(r"^# (\d{3})$")
MARK = "__STEP__"


def report(line: str) -> None:
    """One line on stdout."""
    sys.stdout.write(f"{line}\n")


def steps(readme: str) -> list[tuple[str, str | None]]:
    """Each command with the status the README shows after it, if any."""
    match = BLOCK.search(readme)
    if match is None:
        message = "README has no walkthrough block"
        raise SystemExit(message)
    lines = [line for line in match.group(1).splitlines() if line.strip()]
    found: list[tuple[str, str | None]] = []
    for line in lines:
        status = STATUS.match(line)
        if status and found:
            found[-1] = (found[-1][0], status.group(1))
        elif not line.startswith("#"):
            found.append((line, None))
    return found


def script(found: list[tuple[str, str | None]], base: str, jar: Path) -> str:
    """A bash script that runs every step and prints a marker before each output."""
    body = ["set -uo pipefail"]
    for index, (command, _) in enumerate(found):
        line = command.replace("jar.txt", str(jar))
        if line.startswith("BASE="):
            line = f"BASE={base}/api/v1"
        body.append(f"echo {MARK}{index}")
        body.append(line)
    return "\n".join(body) + "\n"


def summary(output: str) -> str:
    """The status line and the body's status or error code, never the body itself."""
    lines = output.strip().splitlines()
    if not lines:
        return "(no output)"
    detail = ""
    try:
        body = json.loads("\n".join(lines[:-1]))
        data, error = body.get("data"), body.get("error")
        if error:
            detail = f" error.code={error.get('code')}"
        elif isinstance(data, dict) and "status" in data:
            detail = f" data.status={data['status']}"
    except (json.JSONDecodeError, AttributeError):
        detail = ""
    return f"{lines[-1]}{detail}"


def main(base: str) -> bool:
    """Run the walkthrough and compare each shown status."""
    found = steps((ROOT / "README.md").read_text())
    report(f"base: {base}/api/v1 (the README's BASE line is replaced by this)")
    with tempfile.TemporaryDirectory() as folder:
        result = subprocess.run(
            ["/usr/bin/env", "bash"],
            input=script(found, base, Path(folder) / "jar.txt"),
            capture_output=True,
            text=True,
            cwd=ROOT,
            timeout=300,
            check=False,
        )
    outputs = re.split(rf"^{MARK}\d+$\n?", result.stdout, flags=re.MULTILINE)[1:]
    passed = len(outputs) == len(found)
    for (command, expected), output in zip(found, outputs, strict=False):
        shown = output.strip().splitlines()[-1] if output.strip() else ""
        ok = expected is None or shown == expected
        passed = passed and ok
        tail = f" -> {summary(output)} (README shows {expected})" if expected else ""
        report(f"{'ok  ' if ok else 'FAIL'} $ {command.replace('jar.txt', 'jar')}{tail}")
    if result.stderr.strip():
        report(f"stderr: {result.stderr.strip().splitlines()[-1]}")
    report(f"result: {'PASSED' if passed else 'FAILED'}")
    return passed


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit(__doc__)
    sys.exit(0 if main(sys.argv[1].rstrip("/")) else 1)
