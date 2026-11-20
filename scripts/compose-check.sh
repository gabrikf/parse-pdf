#!/usr/bin/env bash
# Criterion 1's proof: a clean checkout of HEAD, with .env copied from .env.example and only
# SESSION_SECRET set, brings redis, storage, api, worker and web to healthy, and api and worker
# wait for redis and storage with `condition: service_healthy`.
#   scripts/compose-check.sh            (uses WEB_PORT 8082 and project parse-pdf-clean)
set -euo pipefail

root="$(cd "$(dirname "$0")/.." && pwd)"
project="parse-pdf-clean"
checkout="$(mktemp -d)"
trap 'docker compose -p "$project" --project-directory "$checkout" down -v --remove-orphans >/dev/null 2>&1 || true; rm -rf "$checkout"' EXIT

git -C "$root" archive HEAD | tar -x -C "$checkout"
cp "$checkout/.env.example" "$checkout/.env"
secret="$(python3 -c 'import secrets; print(secrets.token_urlsafe(48))')"
sed -i "s|^SESSION_SECRET=.*|SESSION_SECRET=${secret}|; s|^WEB_PORT=.*|WEB_PORT=8082|" "$checkout/.env"
echo "checkout: git archive $(git -C "$root" rev-parse --short HEAD), .env from .env.example, SESSION_SECRET generated (not printed), WEB_PORT=8082"

cd "$checkout"
docker compose -p "$project" up -d --build --wait --quiet-pull >/dev/null 2>&1
docker compose -p "$project" ps --format '{{.Service}} {{.Status}}' | sort

python3 - "$project" <<'PY'
import json, subprocess, sys
config = json.loads(subprocess.run(["docker", "compose", "-p", sys.argv[1], "config", "--format", "json"], capture_output=True, text=True, check=True).stdout)
failed = False
for service in ("api", "worker"):
    depends = config["services"][service].get("depends_on", {})
    conditions = {name: depends.get(name, {}).get("condition") for name in ("redis", "storage")}
    print(f"{service} depends_on: {conditions}")
    failed |= any(value != "service_healthy" for value in conditions.values())
states = subprocess.run(["docker", "compose", "-p", sys.argv[1], "ps", "--format", "json"], capture_output=True, text=True, check=True).stdout
health = {json.loads(line)["Service"]: json.loads(line)["Health"] for line in states.splitlines() if line.strip()}
for service in ("redis", "storage", "api", "worker", "web"):
    failed |= health.get(service) != "healthy"
print("result:", "FAILED" if failed else "PASSED")
sys.exit(1 if failed else 0)
PY
