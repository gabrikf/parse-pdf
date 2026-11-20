# Harness provenance

Where each vendored skill came from and why it was picked. Copied from the `pdf-parser` repo on
2026-11-19; install counts and dates are the ones recorded there. All skills now live in
`.claude/skills/` (they were split between `.agents/skills/` and `.cursor/skills/`), so the install
commands use `-a claude-code`. Hashes are in `../skills-lock.json`.

## Changes from the pdf-parser harness

- One skills folder, `.claude/skills/`, read by Claude Code and by Cursor.
- `.cursor/rules/laws.mdc` merged into `AGENTS.md` (Laws). It said 80% coverage while the gate
  enforced 85%, and it named a `backend/eslint.config.js` that never existed; both fixed.
- `delivery-check.sh` (Stop hook) dropped. It always printed `not_run` / `passed: false`, so it
  added noise every turn and checked nothing.
- `eslint-backend.sh` (which ran ruff) and `eslint-frontend.sh` merged into
  `scripts/hooks/after-edit.sh`, which reads both the Claude Code and the Cursor hook payloads, adds
  `ruff format --check`, and runs only in phase `implement` (`scripts/phase.sh`).
- `pre-commit` runs only the side whose code is staged, so planning commits run nothing and a repo
  without a frontend yet can still commit backend code.
- Coverage gate reads the package from `backend/pyproject.toml` instead of hard-coding `pdf_parser`.
- `/review-before-push` skill added: runs the review script, the six lanes as parallel subagents,
  and the `code-polish` judge in the main session.

## Writing and process skills

React performance skill `react`, project scope, copied. It applies to the frontend. The frontend follows it. The target release is React 19.3.1, the current `react` version on npm on 2026-11-14.

- Path: [`.claude/skills/react/SKILL.md`](../.claude/skills/react/SKILL.md)
- Source: [PyModel/react-frontend-skills](https://github.com/PyModel/react-frontend-skills) (`skills/react`), lock file `skills-lock.json`
- Install: `npx skills add https://github.com/PyModel/react-frontend-skills --skill react -a claude-code -y --copy`
- Why this one: the skill is a React 19 performance guide (44 rules) and covers the React 19.3 stabilizations (`ViewTransition`, Fragment refs, `use(browser())`). The upstream README states a re-audit on 2026-11-09 against `react` 19.3.1. On 2026-11-14, skills.sh listed this skill at 663 installs, the highest count among React performance skills that name the 19.3 release. `vercel-labs/agent-skills` skill `vercel-react-best-practices` had about 899.4K installs and covers React 19 in general; it does not target 19.3. `lu1sdv/skillsmd` skill `react-performance` baselines React 19.3 and had about 1 install.

Visual identity skill `frontend-design`, project scope, copied. It applies to the upload page. The page follows it for palette, type, and layout.

- Path: [`.claude/skills/frontend-design/SKILL.md`](../.claude/skills/frontend-design/SKILL.md)
- Source: [anthropics/skills](https://github.com/anthropics/skills) (`skills/frontend-design`), lock file `skills-lock.json`, commit `e4bb5d960d87126ff3b3a8af1a104b7db67560ba`
- Install: `npx skills add https://github.com/anthropics/skills --skill frontend-design -a claude-code -y --copy`
- Why this one: on 2026-11-17, skills.sh listed `frontend-design` at 1.1M installs, the highest count among skills whose job is a deliberate palette, type, and layout instead of a generic template. `web-design-guidelines` is the interaction audit and does not choose a look. `ui-ux-pro-max` (`nextlevelbuilder/ui-ux-pro-max-skill`) was about 453K installs and is a style database, below both. An MCP was the worse fit: the design draws no screen, and this repo already copies skills rather than calling a design server.

UX skill `web-design-guidelines`, project scope, copied. It applies to the upload page. The page follows it for focus, keyboard, paste, labels, errors, and hit area.

- Path: [`.claude/skills/web-design-guidelines/SKILL.md`](../.claude/skills/web-design-guidelines/SKILL.md)
- Source: [vercel-labs/agent-skills](https://github.com/vercel-labs/agent-skills) (`skills/web-design-guidelines`), lock file `skills-lock.json`, commit `1a2c79d4e6c4a2283dc2c614b6538cbe1ed5ca62`
- Install: `npx skills add https://github.com/vercel-labs/agent-skills --skill web-design-guidelines -a claude-code -y --copy`
- Why this one: on 2026-11-17, skills.sh listed `web-design-guidelines` at 870.4K installs, the highest count among skills that apply a published interface rule set. The rules are Vercel's Web Interface Guidelines, fetched from `https://raw.githubusercontent.com/vercel-labs/web-interface-guidelines/main/command.md`. `frontend-design` is higher overall and chooses the look; it does not review keyboard, paste, focus, or error placement. This skill is not the vercel-labs/ui behavior kit. The design still rejects that kit.

Clean code skill `clean-code`, project scope, copied. It applies to the frontend and the backend.

- Path: [`.claude/skills/clean-code/SKILL.md`](../.claude/skills/clean-code/SKILL.md)
- Source: [sickn33/agentic-awesome-skills](https://github.com/sickn33/agentic-awesome-skills) (`skills/clean-code`), lock file `skills-lock.json`
- Install: `npx skills add https://github.com/sickn33/agentic-awesome-skills --skill clean-code -a claude-code -y --copy`
- Why this one: on 2026-11-14, skills.sh listed this skill at 12.9K installs. It is Uncle Bob clean-code guidance for names, functions, errors, and tests, and it is not tied to one language.

SOLID skill `solid`, project scope, copied. It applies to the backend only.

- Path: [`.claude/skills/solid/SKILL.md`](../.claude/skills/solid/SKILL.md)
- Source: [ramziddin/solid-skills](https://github.com/ramziddin/solid-skills) (`skills/solid`), lock file `skills-lock.json`
- Install: `npx skills add https://github.com/ramziddin/solid-skills --skill solid -a claude-code -y --copy`
- Why this one: on 2026-11-14, skills.sh listed `ramziddin/solid-skills` skill `solid` at 3,664 installs (about 3.7K on the directory page). That is the highest install count among skills whose subject is the SOLID principles. The next skill named `solid-principles` (`thebushidocollective/han`) had 605 installs. Higher matches such as `solidity-security` are the Solidity language, not SOLID. Invoke it by name (`solid`) or when writing, reviewing, or designing backend code.

Tech Leads Club skills, project scope, copied. Reinstall with `npx @tech-leads-club/agent-skills@1.6.3 install -s tlc-spec-lean tlc-discover tlc-implement tlc-plan -a claude-code` (no `-g`). In pdf-parser they were installed with `-a cursor`. This machine is Node v22; the package asked for Node >= 24 and warned; the install still completed.

| Skill | Version | Path |
| --- | --- | --- |
| `tlc-spec-lean` | 2.2.0 | `.claude/skills/tlc-spec-lean` |
| `tlc-discover` | 0.10.0 | `.claude/skills/tlc-discover` |
| `tlc-plan` | 1.1.1 | `.claude/skills/tlc-plan` |
| `tlc-implement` | 1.2.0 | `.claude/skills/tlc-implement` |

Invoke one by naming it (`tlc-spec-lean`, `tlc-discover`, `tlc-plan`, `tlc-implement`) or with the phrases in that skill's description. Read `.claude/skills/<name>/SKILL.md` and follow it.

## Review skills

These are review skills. They sit next to `react`, `clean-code`, and `solid`. Those three stay as they are. The clean-code lane is the `clean-code` skill already installed. A second clean-code skill was not added: `addyosmani/agent-skills` `code-simplification` had 77.3K installs on 2026-11-17 and overlaps the installed skill. Two simplifiers would give the judge two ways to rewrite the same lines.

Counts below are from skills.sh on 2026-11-17 unless a date is stated. Install commands use the same flags as the skills already in this repo.

Frontend review skill `typescript-react-reviewer`, project scope, copied. Use it on `frontend/` TypeScript and JavaScript.

- Path: [`.claude/skills/typescript-react-reviewer/SKILL.md`](../.claude/skills/typescript-react-reviewer/SKILL.md)
- Source: [dotneet/claude-code-marketplace `review-tool/skills/typescript-react-reviewer/SKILL.md`](https://github.com/dotneet/claude-code-marketplace/blob/main/review-tool/skills/typescript-react-reviewer/SKILL.md)
- Install: `npx skills add https://github.com/dotneet/claude-code-marketplace --skill typescript-react-reviewer -a claude-code -y --copy`
- Why this one: it reviews TypeScript and React 19, leads with bugs that block a merge, and each pattern has the wrong code and the correct code. On 2026-11-17, skills.sh listed it at 9.0K installs. `langgenius/dify` `frontend-code-review` had about 10.1K installs and only reviews files under `web/` or `packages/dify-ui/`. `mattpocock/skills` `code-review` had about 142K installs on 2026-10-15. It checks standards and the spec in two sub-agents, and it does not drop weak findings or give a defect fix. `giuseppe-trisciuoglio/developer-kit` `react-code-review` had 1.5K installs and hands the review to an architect agent. The React 19.3 performance guide stays [`.claude/skills/react/SKILL.md`](../.claude/skills/react/SKILL.md). `vercel-react-best-practices` is not installed. It is a writing catalog, and this repo already records why it is not the React 19.3 skill.

Backend review skill `python-anti-patterns`, project scope, copied. Use it on Python. Backend design stays with `solid`.

- Path: [`.claude/skills/python-anti-patterns/SKILL.md`](../.claude/skills/python-anti-patterns/SKILL.md)
- Source: [wshobson/agents `plugins/python-development/skills/python-anti-patterns/SKILL.md`](https://github.com/wshobson/agents/blob/main/plugins/python-development/skills/python-anti-patterns/SKILL.md)
- Install: `npx skills add https://github.com/wshobson/agents --skill python-anti-patterns -a claude-code -y --copy`
- Why this one: the package under review is `pdf_parser`. This skill is a Python review checklist, and each item shows the bad code and the fix. On 2026-11-17, skills.sh listed it at 14.0K installs on the `wshobson/agents` page. `langgenius/dify` `backend-code-review` (2.1K) only reviews that repo's `api/` tree and points at SQLAlchemy docs this repo does not have. `ruicore/codex-skills` `python-backend-review` had 8 installs. `getsentry/skills` `code-review` is written for Sentry's Django code.

Security review skill `security-review`, project scope, copied.

- Path: [`.claude/skills/security-review/SKILL.md`](../.claude/skills/security-review/SKILL.md)
- Source: [getsentry/skills `skills/security-review/SKILL.md`](https://github.com/getsentry/skills/blob/main/skills/security-review/SKILL.md)
- Install: `npx skills add https://github.com/getsentry/skills --skill security-review -a claude-code -y --copy`
- Why this one: it reports a finding only when the pattern is high confidence and the input is attacker-controlled, and the finding format has a Fix line. Low-confidence notes are not reported. It loads the guide for the kind of code in the diff, not every guide. On 2026-11-17, skills.sh listed it at 23.8K installs, the highest dedicated security review. `addyosmani/agent-skills` `security-and-hardening` had 86.7K installs and is a hardening guide (threat model, then build). The skills in that catalog sat between 46.8K and 89.3K installs, which is what a full-catalog install produces. The skills CLI reported Gen Safe, Socket 1 alert, and Snyk low risk for this copy. The alert matches the exploit examples in the skill (`eval`, a sample key). The copied files do not fetch a URL.

UX, UI, and responsiveness skill `web-design-guidelines`, project scope, copied. Use it on frontend TSX, JSX, and CSS.

- Path: [`.claude/skills/web-design-guidelines/SKILL.md`](../.claude/skills/web-design-guidelines/SKILL.md)
- Source: [vercel-labs/agent-skills `skills/web-design-guidelines/SKILL.md`](https://github.com/vercel-labs/agent-skills/blob/main/skills/web-design-guidelines/SKILL.md)
- Install: `npx skills add https://github.com/vercel-labs/agent-skills --skill web-design-guidelines -a claude-code -y --copy`
- Why this one: it reviews UI code and prints terse `file:line` findings. The line is the fix (`transition: all` becomes a listed property, an icon button needs an `aria-label`). The fetched guidelines cover focus, forms, touch, safe areas, overflow, long text, and layout, which is the responsiveness check. On 2026-11-17, the vercel-labs catalog on skills.sh listed it at 870.6K installs. A 90-checkpoint full-stack audit is slower and mixes SEO and payments into the review. `addyosmani/agent-skills` `frontend-ui-engineering` (82.8K) tells the agent how to build a page, not how to report `file:line` findings.

Performance and good practices skill `performance-optimization`, project scope, copied.

- Path: [`.claude/skills/performance-optimization/SKILL.md`](../.claude/skills/performance-optimization/SKILL.md)
- Source: [addyosmani/agent-skills `skills/performance-optimization/SKILL.md`](https://github.com/addyosmani/agent-skills/blob/main/skills/performance-optimization/SKILL.md)
- Install: `npx skills add https://github.com/addyosmani/agent-skills --skill performance-optimization -a claude-code -y --copy`
- Why this one: it covers frontend and backend cost, and it refuses a fix that was not measured or pointed at a real bottleneck. On 2026-11-17, skills.sh listed it at 80.0K installs. `wshobson/agents` `python-performance-optimization` had 38.0K installs and is a Python profiling guide, so it misses the React UI. The React 19.3 rules stay in the `react` skill above. The pre-push command tells the agent to suggest a performance fix only for a concrete cost in the diff (an N+1 loop, an unbounded read, a layout read in render, an image with no width and height).

Judge skill `code-polish`, project scope, copied. This is the step that drops weak findings and applies the ones worth fixing.

- Path: [`.claude/skills/code-polish/SKILL.md`](../.claude/skills/code-polish/SKILL.md)
- Source: [PaulRBerg/agent-skills `skills/code-polish/SKILL.md`](https://github.com/PaulRBerg/agent-skills/blob/main/skills/code-polish/SKILL.md)
- Install: `npx skills add https://github.com/PaulRBerg/agent-skills --skill code-polish -a claude-code -y --copy`
- Why this one: `--review` keeps a fix only when the location, the triggering input, the failure, and the blast radius are in the diff, then it applies the smallest fix. It stops when it cannot show that behavior stayed the same, and it leaves that item Open. On 2026-11-17, skills.sh listed it at 2.8K installs. `aictrl-dev/skills` `judge-review-findings` sorts findings into fix, defer, and ignore, and it forbids editing. `wshobson/agents` `multi-reviewer-patterns` (10.3K) keeps low findings and, on a conflict, takes the higher severity. `everyinc/compound-engineering-plugin` `ce-code-review` (about 2.3K on 2026-10-15) fans out to several agents, can send the diff to another model, and writes a docs tree. That is the wrong shape for this repo. `code-polish` does not read another skill's report on its own. The command below tells the agent to hold the lane findings to that bar.
