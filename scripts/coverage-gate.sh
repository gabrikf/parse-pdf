#!/usr/bin/env bash
# Backend coverage gate: line + branch coverage at or above 85%.
# The measured package is set once in backend/pyproject.toml:
#   [tool.coverage.run]
#   source = ["<package>"]
#   branch = true
set -euo pipefail

root="$(cd "$(dirname "$0")/.." && pwd)"
cd "$root/backend"

py=""
for candidate in "$root/.venv/bin/python" "$root/backend/.venv/bin/python"; do
  if [[ -x "$candidate" ]]; then
    py="$candidate"
    break
  fi
done
py="${py:-${PYTHON:-python3}}"

"$py" -m pytest --cov --cov-branch --cov-report=term-missing --cov-fail-under=85
