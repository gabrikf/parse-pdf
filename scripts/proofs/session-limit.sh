#!/usr/bin/env bash
# Criterion 17: the sessions-per-IP limit holds when the client writes its own X-Forwarded-For
# (nginx overwrites the header). Output goes to evidence/session-limit/.
set -euo pipefail

root="$(cd "$(dirname "$0")/../.." && pwd)"
evidence="${EVIDENCE_DIR:-$root/evidence}"  # AD-038: check_proofs runs write outside the repo
base="$("$root/scripts/proofs/e2e-stack.sh")"
# The e2e stack raises the limit for its parallel tests (AD-032): read the one the API runs with.
limit="$(docker compose -p parse-pdf-e2e exec -T api printenv SESSIONS_PER_MINUTE_PER_IP || echo 20)"
mkdir -p "$evidence/session-limit"
python3 "$root/scripts/proofs/session_limit.py" "$base" "$limit" | tee "$evidence/session-limit/run.txt"
