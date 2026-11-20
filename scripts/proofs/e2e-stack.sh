#!/usr/bin/env bash
# Bring up (or reuse) the e2e stack: compose.yaml + compose.e2e.yaml, models on the local stub,
# never the real OpenRouter key. Prints the base URL. WORKERS sets the worker count (default 3).
set -euo pipefail

root="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$root"
# A fixed, public value: the e2e stack signs only throwaway test sessions.
export SESSION_SECRET="e2e-session-secret-not-a-real-secret-0123456789"
docker compose -p parse-pdf-e2e -f compose.yaml -f compose.e2e.yaml \
  up -d --build --wait --quiet-pull --scale worker="${WORKERS:-3}" >/dev/null 2>&1
echo "http://localhost:${WEB_PORT:-8081}"
