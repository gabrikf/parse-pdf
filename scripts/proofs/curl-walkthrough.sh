#!/usr/bin/env bash
# Criterion 78: run the README curl walkthrough against the e2e stack (models on the local stub)
# and check every status the README shows. Output goes to evidence/curl-walkthrough/.
set -euo pipefail

root="$(cd "$(dirname "$0")/../.." && pwd)"
base="$("$root/scripts/proofs/e2e-stack.sh")"
mkdir -p "$root/evidence/curl-walkthrough"
python3 "$root/scripts/proofs/curl_walkthrough.py" "$base" | tee "$root/evidence/curl-walkthrough/run.txt"
