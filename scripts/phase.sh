#!/usr/bin/env bash
# Work phase for this checkout. The agent edit hooks run only in `implement`.
#   scripts/phase.sh                 print the current phase
#   scripts/phase.sh discover|plan|implement
# State lives in .harness/phase (gitignored, one per worktree). No file means `plan`.
set -euo pipefail

root="$(cd "$(dirname "$0")/.." && pwd)"
file="$root/.harness/phase"

if [[ $# -eq 0 ]]; then
  if [[ -f "$file" ]]; then cat "$file"; else echo plan; fi
  exit 0
fi

case "$1" in
  discover | plan | implement) ;;
  *)
    echo "usage: scripts/phase.sh [discover|plan|implement]" >&2
    exit 64
    ;;
esac

mkdir -p "$root/.harness"
printf '%s\n' "$1" >"$file"
echo "phase: $1"
if [[ "$1" == implement ]]; then
  echo "agent edit hooks: on (ESLint for frontend/, ruff for backend/)"
else
  echo "agent edit hooks: off"
fi
