#!/usr/bin/env bash
# Pre-push review prompt. Prints the agent command for the commits being pushed.
# Does not call a model, does not drop findings, and does not edit code.
# `passed: false` is not a pass. A person runs the printed command.
set -euo pipefail

root="$(cd "$(dirname "$0")/.." && pwd)"
cd "$root"

files_text=""
range_notes=""

add_diff() {
  local from="$1"
  local to="$2"
  local chunk
  chunk="$(git diff --name-only "$from" "$to" 2>/dev/null || true)"
  if [[ -n "$chunk" ]]; then
    files_text+="$chunk"$'\n'
  fi
}

consider_record() {
  local local_ref="$1"
  local local_sha="$2"
  local remote_ref="$3"
  local remote_sha="$4"
  local chunk
  if [[ "$local_sha" =~ ^0+$ ]]; then
    range_notes+="delete ${local_ref}"$'\n'
    return
  fi
  if [[ "$remote_sha" =~ ^0+$ ]]; then
    if git rev-parse --verify origin/main >/dev/null 2>&1; then
      local base
      base="$(git merge-base origin/main "$local_sha")"
      range_notes+="${base}..${local_sha} ${local_ref} (new remote ${remote_ref})"$'\n'
      add_diff "$base" "$local_sha"
    else
      range_notes+="${local_sha} ${local_ref} (no origin/main)"$'\n'
      chunk="$(git diff-tree --no-commit-id --name-only -r "$local_sha" 2>/dev/null || true)"
      if [[ -n "$chunk" ]]; then
        files_text+="$chunk"$'\n'
      fi
    fi
    return
  fi
  range_notes+="${remote_sha}..${local_sha} ${local_ref}"$'\n'
  add_diff "$remote_sha" "$local_sha"
}

use_head_range() {
  if git rev-parse --verify origin/main >/dev/null 2>&1; then
    local base
    base="$(git merge-base origin/main HEAD)"
    range_notes+="${base}..HEAD"$'\n'
    add_diff "$base" HEAD
  else
    range_notes+="HEAD"$'\n'
    add_diff HEAD HEAD
  fi
}

if [[ $# -eq 2 ]]; then
  range_notes+="$1..$2"$'\n'
  add_diff "$1" "$2"
elif [[ -t 0 ]]; then
  use_head_range
else
  got_record=0
  while read -r local_ref local_sha remote_ref remote_sha; do
    [[ -n "${local_sha:-}" ]] || continue
    got_record=1
    consider_record "$local_ref" "$local_sha" "$remote_ref" "$remote_sha"
  done
  if [[ "$got_record" -eq 0 ]]; then
    use_head_range
  fi
fi

mapfile -t files < <(printf '%s' "$files_text" | sed '/^$/d' | sort -u)

is_code() {
  case "$1" in
    .claude/* | .cursor/* | .harness/* | .design/* | .specs/* | docs/* | evidence/*) return 1 ;;
    .githooks/* | *.py | *.ts | *.tsx | *.js | *.jsx | *.mjs | *.cjs | *.css | *.scss | *.sh) return 0 ;;
    *) return 1 ;;
  esac
}

code_files=()
frontend_files=()
ui_files=()
python_files=()
backend_design_files=()
for f in "${files[@]}"; do
  is_code "$f" || continue
  code_files+=("$f")
  case "$f" in
    *.py) python_files+=("$f") ;;
  esac
  case "$f" in
    frontend/*.ts | frontend/*.tsx | frontend/*.js | frontend/*.jsx | frontend/*.mjs | frontend/*.cjs)
      frontend_files+=("$f")
      ;;
  esac
  case "$f" in
    frontend/*.tsx | frontend/*.jsx | frontend/*.css | frontend/*.scss)
      ui_files+=("$f")
      ;;
  esac
  case "$f" in
    *.py | backend/*.ts | backend/*.tsx | backend/*.js | backend/*.jsx | backend/*.mjs | backend/*.cjs)
      backend_design_files+=("$f")
      ;;
  esac
done

print_files() {
  local label="$1"
  shift
  echo "$label"
  if [[ $# -eq 0 ]]; then
    echo "(none — skip this lane)"
    return
  fi
  local f
  for f in "$@"; do
    echo "- $f"
  done
}

if [[ ${#code_files[@]} -eq 0 ]]; then
  echo "review-skills: status: not_required"
  echo "review-skills: passed: false"
  echo "review-skills: reason: no application code in this push. The review skills did not run. not_required is not a pass."
  echo "review-skills: ranges:"
  if [[ -n "$range_notes" ]]; then
    printf '%s' "$range_notes" | sed '/^$/d' | sed 's/^/  /'
  else
    echo "  (none)"
  fi
  exit 0
fi

echo "review-skills: status: not_run"
echo "review-skills: passed: false"
echo "review-skills: reason: these skills are agent instructions. This hook does not call a model, does not drop findings, and does not edit code. not_run is not a pass."
echo "review-skills: ranges:"
printf '%s' "$range_notes" | sed '/^$/d' | sed 's/^/  /'
echo "review-skills: command: in Claude Code run /review-before-push (or paste the block below to the agent). A person still confirms every applied fix."
echo
echo "Review only the files listed in each lane. Read that lane's SKILL.md and follow it."
echo "For each finding, keep the fix that skill already gives, plus the file and line."
echo "Do not edit until the judge step."
echo
print_files "1. Frontend — .claude/skills/typescript-react-reviewer/SKILL.md" "${frontend_files[@]+"${frontend_files[@]}"}"
if [[ ${#frontend_files[@]} -gt 0 ]]; then
  echo "   React 19.3 rules stay in .claude/skills/react/SKILL.md. Use them when a finding is about React performance."
fi
echo
print_files "2. Backend — .claude/skills/python-anti-patterns/SKILL.md" "${python_files[@]+"${python_files[@]}"}"
print_files "   Backend design — .claude/skills/solid/SKILL.md" "${backend_design_files[@]+"${backend_design_files[@]}"}"
echo
print_files "3. Security — .claude/skills/security-review/SKILL.md" "${code_files[@]+"${code_files[@]}"}"
echo "   Report only high-confidence findings. Each one already has a Fix line. Do not report low-confidence notes."
echo
print_files "4. UX, UI, and responsiveness — .claude/skills/web-design-guidelines/SKILL.md" "${ui_files[@]+"${ui_files[@]}"}"
echo
print_files "5. Clean code — .claude/skills/clean-code/SKILL.md" "${code_files[@]+"${code_files[@]}"}"
echo "   Suggest the smaller name, function, or error path. Do not apply it in this lane."
echo
print_files "6. Performance and good practices — .claude/skills/performance-optimization/SKILL.md" "${code_files[@]+"${code_files[@]}"}"
echo "   Suggest a fix only when the file shows a concrete cost (an N+1 loop, an unbounded read, a layout read in render, a missing width and height on an image). Do not invent a performance nit."
echo
echo "7. Judge — .claude/skills/code-polish/SKILL.md --review"
echo "   Hold every finding from the lanes above to this bar:"
echo "   - Drop it when it has no file and line in the list above, when confidence is low, when it is a nit, or when ESLint or Sonar already enforces it."
echo "   - Drop it when the lane cannot show the failure from the cited lines."
echo "   - Apply the lane's suggested fix only when it cites a file and line, names the failure, and does not change a public contract."
echo "   - Leave the rest for a person. That includes anything this skill would mark Open because behavior was not verified."
echo "   Do not run --simplify in this step."
echo
echo "What still needs a person: run this command, read the judge's Open items, and confirm each applied fix. The git hook cannot do that. There is no API key in this repo, and the hook must not pretend a model ran."
