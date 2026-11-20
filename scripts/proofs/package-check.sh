#!/usr/bin/env bash
# Criterion 79: the delivery zip holds no .venv, node_modules, .env, .specs, .claude or evidence
# file, and does hold what a reviewer needs. Output goes to evidence/package/.
set -euo pipefail

root="$(cd "$(dirname "$0")/../.." && pwd)"
work="$(mktemp -d)"
trap 'rm -rf "$work"' EXIT
mkdir -p "$root/evidence/package"
log="$root/evidence/package/package-check.txt"

"$root/scripts/package.sh" "$work/parse-pdf.zip" >/dev/null
unzip -Z1 "$work/parse-pdf.zip" > "$work/entries.txt"
failed=0
{
  echo "zip: $(wc -l < "$work/entries.txt") entries, $(du -h "$work/parse-pdf.zip" | cut -f1)"
  for pattern in '/\.venv/' '/node_modules/' '/\.env$' '/\.specs/' '/\.claude/' '/evidence/'; do
    count="$(grep -cE "$pattern" "$work/entries.txt" || true)"
    if [[ "$count" == "0" ]]; then echo "ok   no entry matches $pattern"; else echo "FAIL $count entries match $pattern"; failed=1; fi
  done
  for needed in parse-pdf/README.md parse-pdf/compose.yaml parse-pdf/.env.example \
    parse-pdf/docs/postman/parse-pdf.postman_collection.json parse-pdf/samples/w3c-dummy-locked.pdf \
    parse-pdf/backend/pyproject.toml parse-pdf/frontend/package.json; do
    if grep -qxF "$needed" "$work/entries.txt"; then echo "ok   holds $needed"; else echo "FAIL missing $needed"; failed=1; fi
  done
  if [[ "$failed" == "0" ]]; then echo "result: PASSED"; else echo "result: FAILED"; fi
} | tee "$log"
grep -q "result: PASSED" "$log"
