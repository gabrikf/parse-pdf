#!/usr/bin/env bash
# Criterion 24: Redis restarts with 5 documents queued; all reach ready, no 5xx after.
set -euo pipefail

root="$(cd "$(dirname "$0")/../.." && pwd)"
evidence="${EVIDENCE_DIR:-$root/evidence}"  # AD-038: check_proofs runs write outside the repo
base="$("$root/scripts/proofs/e2e-stack.sh")"
mkdir -p "$evidence/concurrency"
{
  echo "# Criterion 24 Redis restart proof"
  echo "date: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
  echo "commit: $(git -C "$root" rev-parse --short HEAD)"
  echo "command: .venv/bin/python scripts/load/redis_restart.py --base $base --project parse-pdf-e2e"
  echo
  "$root/.venv/bin/python" "$root/scripts/load/redis_restart.py" --base "$base" --project parse-pdf-e2e
} | tee "$evidence/concurrency/redis-restart.txt"
