#!/usr/bin/env bash
# Agent edit hook, shared by Claude Code (PostToolUse) and Cursor (afterFileEdit).
# Runs only when scripts/phase.sh says `implement`. In discover and plan it exits 0 and prints nothing.
#   frontend/*.{ts,tsx,js,jsx,mjs,cjs}  -> ESLint (frontend/eslint.config.js, SonarJS recommended)
#   backend/*.py                        -> ruff check + ruff format --check
# Exit 2 sends the lint output back to Claude Code as feedback on the edit.
set -euo pipefail

root="$(cd "$(dirname "$0")/../.." && pwd)"

phase="plan"
[[ -f "$root/.harness/phase" ]] && phase="$(tr -d '[:space:]' <"$root/.harness/phase")"
[[ "$phase" == implement ]] || exit 0

input="$(cat || true)"
file="$(printf '%s' "$input" | python3 -c '
import json, sys
raw = sys.stdin.read().strip()
try:
    data = json.loads(raw) if raw else {}
except json.JSONDecodeError:
    data = {}
# Claude Code: tool_input.file_path. Cursor: file_path.
tool_input = data.get("tool_input") or {}
print(tool_input.get("file_path") or data.get("file_path") or "")
')"

[[ -n "$file" && -f "$file" ]] || exit 0
case "$file" in
  /*) ;;
  *) file="$root/$file" ;;
esac

find_tool() {
  local name="$1" dir
  for dir in "$root/.venv/bin" "$root/backend/.venv/bin"; do
    if [[ -x "$dir/$name" ]]; then
      echo "$dir/$name"
      return
    fi
  done
  command -v "$name" || true
}

lint_frontend() {
  local eslint="$root/frontend/node_modules/.bin/eslint"
  if [[ ! -x "$eslint" ]]; then
    echo "frontend ESLint is not installed. Run: npm ci --prefix frontend" >&2
    exit 2
  fi
  (cd "$root/frontend" && "$eslint" --no-error-on-unmatched-pattern "$file") >&2 || exit 2
}

lint_backend() {
  local ruff
  ruff="$(find_tool ruff)"
  if [[ -z "$ruff" ]]; then
    echo "ruff is not installed. Install the backend dev dependencies (see AGENTS.md, Setup)." >&2
    exit 2
  fi
  (cd "$root/backend" && "$ruff" check "$file" && "$ruff" format --check "$file") >&2 || exit 2
}

case "$file" in
  "$root"/frontend/node_modules/*) exit 0 ;;
  "$root"/frontend/*.ts | "$root"/frontend/*.tsx | "$root"/frontend/*.js | "$root"/frontend/*.jsx | \
    "$root"/frontend/*.mjs | "$root"/frontend/*.cjs)
    lint_frontend
    ;;
  "$root"/backend/*.py) lint_backend ;;
  *) exit 0 ;;
esac
