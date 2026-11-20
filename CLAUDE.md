@AGENTS.md

## Claude Code

- Check the phase (`scripts/phase.sh`) before editing code. If it is not `implement` and the task
  is to write code, run `scripts/phase.sh implement` first and say so in one line.
- The edit hook's lint output arrives as feedback on the edit. Fix the cause in the same turn.
- `tlc-implement` and `tlc-spec-lean` call for a Verifier and a screens reviewer that are not the
  author: run each as a fresh subagent (Agent tool), never in this session.
- Frontend proof: use the browser against the Vite dev server (`.claude/launch.json` once the
  frontend exists) and write the record to `evidence/<requirement-slug>/`.
