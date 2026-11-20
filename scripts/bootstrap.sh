#!/usr/bin/env bash
# One command from a fresh clone to a running app: `make bootstrap` or `npm run bootstrap`.
#
# Steps, each safe to repeat:
#   1. check Docker, Compose v2 and curl
#   2. create .env from .env.example, generate SESSION_SECRET, add any new variables
#   3. pull the images we do not build (redis, seaweedfs), only when missing
#   4. build the api/worker and web images (cached when nothing changed)
#   5. migrations and seeds: none to run (see the step's message)
#   6. start every service and wait until each healthcheck passes
#   7. ask the API whether Redis, storage and OpenRouter are ready
#
# Options:
#   --pull      pull the newest redis and seaweedfs images even when present
#   --no-cache  rebuild our images from scratch
#   -h, --help  show this help
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

PULL_POLICY="missing"
BUILD_ARGS=()
WAIT_TIMEOUT=240

if [[ -t 1 && -z "${NO_COLOR:-}" ]]; then
  BOLD=$'\033[1m'; GREEN=$'\033[32m'; YELLOW=$'\033[33m'; RED=$'\033[31m'; RESET=$'\033[0m'
else
  BOLD=""; GREEN=""; YELLOW=""; RED=""; RESET=""
fi

step() { printf '\n%s==> %s%s\n' "$BOLD" "$1" "$RESET"; }
ok() { printf '%s  ok%s  %s\n' "$GREEN" "$RESET" "$1"; }
warn() { printf '%s  !!%s  %s\n' "$YELLOW" "$RESET" "$1"; }
fail() { printf '%s  xx  %s%s\n' "$RED" "$1" "$RESET" >&2; exit 1; }

usage() { sed -n '2,19p' "$0" | sed 's/^# \{0,1\}//'; }

parse_args() {
  while [[ $# -gt 0 ]]; do
    case "$1" in
      --pull) PULL_POLICY="always" ;;
      --no-cache) BUILD_ARGS+=("--no-cache") ;;
      -h | --help) usage; exit 0 ;;
      *) usage; fail "unknown option: $1" ;;
    esac
    shift
  done
}

# Value of KEY in .env, empty when unset. Never printed.
env_value() {
  grep -E "^$1=" .env | tail -n 1 | cut -d= -f2- || true
}

random_secret() {
  if command -v openssl >/dev/null 2>&1; then
    openssl rand -hex 32
  else
    python3 -c 'import secrets; print(secrets.token_hex(32))'
  fi
}

check_prerequisites() {
  step "1/7  Checking Docker"

  command -v docker >/dev/null 2>&1 || fail "Docker is not installed: https://docs.docker.com/get-docker/"
  docker info >/dev/null 2>&1 || fail "Docker is installed but not running. Start Docker, then run this again."
  docker compose version >/dev/null 2>&1 || fail "Docker Compose v2 is missing (the 'docker compose' plugin)."
  command -v curl >/dev/null 2>&1 || fail "curl is missing; it is used to check the app once it is up."

  ok "$(docker compose version)"
}

prepare_env() {
  step "2/7  Preparing .env"

  if [[ ! -f .env ]]; then
    (umask 077 && cp .env.example .env)
    ok "created .env from .env.example"
  else
    ok ".env already exists, values kept"
  fi

  local key added=0
  while IFS= read -r key; do
    if ! grep -qE "^${key}=" .env; then
      grep -E "^${key}=" .env.example >>.env
      added=$((added + 1))
    fi
  done < <(grep -oE '^[A-Z][A-Z0-9_]*' .env.example)
  [[ $added -gt 0 ]] && ok "added $added new variable(s) from .env.example"

  if [[ -z "$(env_value SESSION_SECRET)" ]]; then
    local secret tmp
    secret="$(random_secret)"
    tmp="$(mktemp)"
    awk -v s="$secret" 'BEGIN{done=0} /^SESSION_SECRET=/{ if(!done){print "SESSION_SECRET=" s; done=1}; next } {print}' .env >"$tmp"
    cat "$tmp" >.env && rm -f "$tmp"
    ok "generated SESSION_SECRET (64 hex characters, not shown)"
  else
    ok "SESSION_SECRET is set"
  fi

  if [[ -z "$(env_value OPENROUTER_API_KEY)" ]]; then
    warn "OPENROUTER_API_KEY is empty: PyPDF works, Gemini, GPT-5 Mini and summaries do not."
    warn "Put a key in .env (https://openrouter.ai/settings/keys) and run this again."
  else
    ok "OPENROUTER_API_KEY is set"
  fi
}

# Only the services that run a public image. `worker` reuses the image `api` builds, so it is
# never pulled.
PULLED_SERVICES=(redis storage)

pull_images() {
  step "3/7  Pulling service images (policy: $PULL_POLICY)"
  docker compose pull --policy "$PULL_POLICY" --quiet "${PULLED_SERVICES[@]}"
  ok "redis and seaweedfs images are present"
}

build_images() {
  step "4/7  Building the backend and web images"
  docker compose build ${BUILD_ARGS[@]+"${BUILD_ARGS[@]}"}
  ok "images built"
}

explain_migrations() {
  step "5/7  Migrations and seeds"
  ok "no migrations: Redis keeps documents as hashes and streams, which need no schema"
  ok "no bucket setup: the API creates the S3 bucket when it starts"
  ok "no seeds: the feed starts empty; sample PDFs to upload are in samples/"
}

check_port_free() {
  local port="$1" owner
  owner="$(docker ps --filter "publish=${port}" --format '{{.Names}}' | head -n 1)"

  if [[ -n "$owner" && "$owner" != "${COMPOSE_PROJECT_NAME:-parse-pdf}-web-"* ]]; then
    fail "port $port is taken by the container '$owner'. Stop it, or set WEB_PORT in .env."
  fi
  if [[ -z "$owner" ]] && (exec 3<>"/dev/tcp/127.0.0.1/${port}") 2>/dev/null; then
    fail "port $port is taken by another program. Free it, or set WEB_PORT in .env."
  fi
}

start_services() {
  local port="$1"
  step "6/7  Starting redis, storage, api, worker and web"

  check_port_free "$port"
  if ! docker compose up --detach --wait --wait-timeout "$WAIT_TIMEOUT"; then
    docker compose ps
    fail "a service did not become healthy in ${WAIT_TIMEOUT}s. See: docker compose logs --tail=50"
  fi
  ok "every service is healthy"
}

check_ready() {
  local port="$1" body
  step "7/7  Asking the API whether it is ready"

  body="$(curl -fsS --max-time 10 "http://localhost:${port}/api/v1/health/ready")" \
    || fail "the API did not answer on http://localhost:${port}/api/v1/health/ready"
  ok "$body"
}

main() {
  parse_args "$@"
  check_prerequisites
  prepare_env

  local port
  # Same precedence as Compose: the shell's WEB_PORT, then .env, then the default.
  port="${WEB_PORT:-$(env_value WEB_PORT)}"
  port="${port:-8080}"

  pull_images
  build_images
  explain_migrations
  start_services "$port"
  check_ready "$port"

  printf '\n%sparse-pdf is running:%s http://localhost:%s\n' "$BOLD" "$RESET" "$port"
  printf '  logs:  make logs    (or docker compose logs -f)\n'
  printf '  stop:  make down    (data is kept in Docker volumes)\n'
}

main "$@"
