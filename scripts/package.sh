#!/usr/bin/env bash
# Build the zip to send: committed files only, the agent harness included.
# No .venv, node_modules, .env or private brief ends up in it: none of them is committed.
set -euo pipefail

root="$(git rev-parse --show-toplevel)"
out="${1:-$root/parse-pdf.zip}"
if [[ -n "$(git -C "$root" status --porcelain)" ]]; then
  echo "warning: uncommitted changes are not included in the archive" >&2
fi
git -C "$root" archive --format=zip --prefix=parse-pdf/ -o "$out" HEAD
echo "wrote $out"
