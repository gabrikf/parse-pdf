#!/usr/bin/env bash
# Criterion 22: 5,000 reads at concurrency 200 and 50 simultaneous uploads on 3 workers.
set -euo pipefail

root="$(cd "$(dirname "$0")/../.." && pwd)"
evidence="${EVIDENCE_DIR:-$root/evidence}"  # AD-038: check_proofs runs write outside the repo
base="$("$root/scripts/proofs/e2e-stack.sh")"
mkdir -p "$evidence/concurrency"
{
  echo "# Criterion 22 load proof"
  echo "date: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
  echo "commit: $(git -C "$root" rev-parse --short HEAD)"
  echo "stack: docker compose -p parse-pdf-e2e -f compose.yaml -f compose.e2e.yaml up -d --build --wait --scale worker=3"
  echo "command: .venv/bin/python scripts/load/load_test.py --base $base --project parse-pdf-e2e"
  echo "services:"
  docker compose -p parse-pdf-e2e ps --format '  {{.Name}} {{.Status}}'
  echo
  "$root/.venv/bin/python" "$root/scripts/load/load_test.py" --base "$base" --project parse-pdf-e2e
} | tee "$evidence/concurrency/load-test.txt"
