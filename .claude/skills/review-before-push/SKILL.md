---
name: review-before-push
description: Run the repo's pre-push code review - six review lanes over the changed files, then the code-polish judge. Use when the user says "review before push", "run the push review", or pastes the output of scripts/review-before-push.sh.
disable-model-invocation: true
argument-hint: "[<from> <to>]"
---

# Review before push

1. Run `scripts/review-before-push.sh $ARGUMENTS`. With no arguments it reviews `origin/main...HEAD`.
2. If it prints `status: not_required`, say so and stop. `not_required` is not a pass.
3. Run each lane that lists files (1 to 6). Lanes are independent: run them as parallel subagents,
   one per lane. Give each subagent only its lane's file list and its `SKILL.md` path, and tell it
   not to edit. Each finding comes back with file, line, the failure, and the fix the skill gives.
4. Run lane 7, the judge, yourself in this session, under `.claude/skills/code-polish/SKILL.md`
   `--review`, holding every lane finding to the bar the script printed.
5. Apply only the fixes the judge keeps. Then run the lint and test commands in AGENTS.md
   (Checks) for each side you touched, and `scripts/coverage-gate.sh` for backend changes.
6. Report: applied fixes (file:line, one line each), dropped findings (count and reason), and the
   Open items left for a person. Do not call the result a pass. A person confirms every applied fix.
