# parse-pdf

New version of the async PDF processor (`pdf-parser`). The assignment is
`docs/private/BWAI2.1_test_task.docx` (local only, gitignored; text in `docs/private/test-task.md`). The backend accepts a PDF, stores it, and a
worker parses it. The upload page has one parser select. Stack: Python FastAPI in `backend/`,
React + Vite + TypeScript in `frontend/`.

The laws below are mandatory. Where each skill came from, and why it was picked over the
alternatives, is in [`docs/harness.md`](docs/harness.md).

## Workflow and phases

Work moves through three phases. The phase gates the agent edit hooks, so lint does not run while
designing or planning.

| Phase | Skill | Writes | Agent edit hooks |
| --- | --- | --- | --- |
| `discover` | `tlc-discover` | `.design/<name>.md` | off |
| `plan` | `tlc-plan` (or the plan step of `tlc-spec-lean`) | `.specs/features/<feature>/plan.md`, `.specs/STATE.md` | off |
| `implement` | `tlc-implement` (or the build step of `tlc-spec-lean`) | code, tests, `evidence/` | on |

- `scripts/phase.sh` prints the phase; `scripts/phase.sh discover|plan|implement` sets it. The value
  is in `.harness/phase`, gitignored, one per checkout or worktree. No file means `plan`.
- Before the first code edit of any implementation (a planned feature, a bug fix, a scaffold), run
  `scripts/phase.sh implement`. When the feature is merged and the next one is being designed, run
  `scripts/phase.sh plan` (or `discover`).
- The git hooks are not phase-gated. They are gated by what is staged: a commit with only docs,
  specs or designs runs nothing; a commit with code runs the gate for that side.

## Laws

1. **Coverage.** Line and branch coverage of the backend package stays at or above 85%. The gate is
   `scripts/coverage-gate.sh` (pytest-cov, `--cov-fail-under=85`). The package is named once in
   `backend/pyproject.toml` under `[tool.coverage.run] source`. A change that fails the gate is not
   done.
2. **Proof.** No requirement is done without proof: the command output of the coverage gate and of
   lint, and, when the requirement shows on a screen, a frontend proof. Unit tests alone do not
   finish a UI requirement.
3. **Frontend proof.** Open the real screen in a browser (the Vite dev server) and compare it to the
   requirement. Record the route, what you did, what the requirement says, and what the screen
   showed.
4. **Evidence.** Write that proof under `evidence/<requirement-slug>/`. No API keys, tokens, or
   secret values in `evidence/`.
5. **Lint.** Frontend TypeScript: ESLint with `@eslint/js` recommended, `typescript-eslint`
   recommended, and `eslint-plugin-sonarjs` recommended (`sonarjs.configs.recommended`) in
   `frontend/eslint.config.js`. Backend Python: ruff (check and format) and `mypy --strict`, config
   in `backend/pyproject.toml`. Lint errors are fixed, not suppressed.
6. **No fake passes.** A check that did not run is reported as not run. `passed: false` and
   `not_required` from the review script are not passes. Do not replace a check with a stub that
   prints success.
7. **Secrets.** Do not commit `.env` or API keys. `.env.example` lists every variable with an empty
   value.

## Hooks

Agent edit hook, one script for both tools: [`scripts/hooks/after-edit.sh`](scripts/hooks/after-edit.sh).

- Claude Code: `.claude/settings.json`, `PostToolUse` on `Edit|Write|MultiEdit`. Lint errors exit 2
  and come back to the agent as feedback on that edit.
- Cursor: `.cursor/hooks.json`, `afterFileEdit`.
- Only in phase `implement`. `frontend/**/*.{ts,tsx,js,jsx,mjs,cjs}` gets ESLint;
  `backend/**/*.py` gets `ruff check` and `ruff format --check`. mypy runs at commit, not per edit.

Git hooks in `.githooks/` (activate once with `git config core.hooksPath .githooks`):

- `pre-commit`: staged frontend code runs ESLint on `frontend/`; staged backend code runs ruff and
  mypy on `backend/`. Nothing else staged, nothing runs.
- `pre-push`: runs `scripts/review-before-push.sh`, which prints the review lanes for the pushed
  files. It calls no model and edits nothing. In Claude Code, run the review with
  `/review-before-push`. A person confirms each applied fix; anything the judge leaves Open stays
  with a person.

## Skills

All skills are vendored in `.claude/skills/` (Claude Code reads them there; Cursor reads
`.claude/skills/` as well). Versions and hashes are in `skills-lock.json`. Do not edit a vendored
skill; reinstall it (commands in `docs/harness.md`).

Process (Tech Leads Club):

- `tlc-discover`: vague idea to design doc. `tlc-plan`: request to one approved plan with EARS
  criteria. `tlc-implement`: approved plan to checks, build, proofs and an independent Verifier.
  `tlc-spec-lean`: plan, build and review in one skill, for a clear feature.

Writing code:

- Frontend: `react` (React 19 performance, 44 rules, targets 19.3), `frontend-design` (palette,
  type, layout of the upload page), `web-design-guidelines` (focus, keyboard, paste, labels,
  errors, hit area).
- Backend: `solid` (design), `python-anti-patterns`.
- Both: `clean-code`.

Review before push (`/review-before-push` runs them in this order):

1. `typescript-react-reviewer`: frontend TS/JS.
2. `python-anti-patterns` and `solid`: backend Python.
3. `security-review`: all code; high-confidence, attacker-controlled findings only.
4. `web-design-guidelines`: frontend TSX, JSX, CSS.
5. `clean-code`: all code; suggest, do not apply.
6. `performance-optimization`: all code; only for a concrete, measured cost in the diff.
7. `code-polish --review`: the judge. Drops weak findings, applies the smallest fix for the rest,
   leaves unverified ones Open.

## Checks

- Backend lint: `ruff check backend && ruff format --check backend && (cd backend && mypy && lint-imports)`
- Backend tests and coverage: `scripts/coverage-gate.sh` (starts `compose.test.yaml` for Redis and
  SeaweedFS; 85% line and branch)
- Frontend lint and types: `npm --prefix frontend run lint` (ESLint with SonarJS) and
  `npm --prefix frontend run typecheck`
- Frontend unit tests: `npm --prefix frontend run test` (vitest)
- End-to-end: `npm --prefix frontend run e2e` (Playwright; brings up `compose.yaml` +
  `compose.e2e.yaml` with the OpenRouter stub on port 8081; report in `evidence/e2e/`)
- Proof scripts: `scripts/proofs/` (concurrency, Redis restart, curl walkthrough, README, package)
  and `scripts/compose-check.sh` (clean checkout)
- Delivery zip: `scripts/package.sh` (committed files only, harness included; `.env`, `.venv`,
  `node_modules` and `docs/private/` are never committed)

The root `package.json` runs `git config core.hooksPath .githooks` on `npm install` (`prepare`).

## Setup

```bash
git config core.hooksPath .githooks
uv venv .venv
uv pip install --python .venv/bin/python -e "./backend[dev]"
npm ci --prefix frontend
```

The edit hook and the commit gate look for ruff and mypy in `.venv/bin`, then `backend/.venv/bin`,
then `PATH`.
