# Review before push: 945baf5..4aa581f

`scripts/review-before-push.sh 945baf5 HEAD` printed 6 lanes and the judge. Each lane ran as a
read-only sub-agent over its own file list; the judge (`code-polish --review`) ran in the build
session against the bar the script printed. This is not a pass.

**Confirmed by the user on 2026-11-20** (asked in the planning session): "Confirm all 6, push".
The 6 applied fixes below (commit `6fa730d`) are confirmed. The Open items were then decided under
AD-023 and fixed in the commit after it (AD-042..AD-047).

| Lane | Skill | Findings |
| --- | --- | --- |
| 1 Frontend | typescript-react-reviewer | 1 |
| 2 Backend | python-anti-patterns, solid | 2 (+2 low, not reported) |
| 3 Security | security-review | 0 |
| 4 UX, UI | web-design-guidelines | 6 |
| 5 Clean code | clean-code (suggest only) | 12 |
| 6 Performance | performance-optimization | 3 (+1 low) |

## Applied (the judge kept these: file and line cited, failure shown, no public contract changed)

- **HIGH** `backend/app/documents/use_cases/upload_documents.py:97` - `asyncio.gather` let the other
  files keep running after one file's storage or Redis write failed; the controller then closed the
  form under them, and their budget stayed reserved. Now a `TaskGroup` cancels them first and the
  first error is re-raised unchanged. Test:
  `tests/unit/test_upload_partial_failure.py::test_one_failed_write_cancels_the_other_files_and_keeps_its_error`
  (fails on the old code: the 2 other writes are never cancelled and 2 pages stay reserved).
- **HIGH** `backend/app/core/isolated.py:49` - cancelling `IsolatedRunner.run` freed the slot while
  the child kept running to its deadline (memory cap exceeded; worker shutdown waited on the
  thread). A cancelled call now kills its child. Test:
  `tests/unit/test_isolated_runner.py::test_a_cancelled_call_kills_its_child_and_frees_the_slot`.
- **HIGH** `frontend/src/shared/api/queryKeys.ts:11`, `ReadyBody.tsx:19` - the page-1 preview was
  cached forever under the document id, so after a reparse the card could show the old parser's page
  1 beside the new summary. The key now carries `updated_at`.
- **MEDIUM** `backend/app/queue/redis_stream_queue.py:79` - `docs:dead` had no cap under
  `noeviction`; it now keeps about the last 10,000 records (`MAXLEN ~`). `docs:stream` is still
  never trimmed (AD-016).
- **MEDIUM** `frontend/src/shared/components/Dialog/Dialog.module.css:4` - from 1024 px a tall dialog
  (20 files) ran 48 px past the screen and its footer could not be reached. Checked on the Vite dev
  server at 1280 x 800 with 20 files: "Upload 20 files" now ends at y 761 of 800.
- **MEDIUM** `frontend/src/pages/UploadPage/components/ConfirmDialog/ConfirmDialog.module.css:1` -
  on a phone held sideways the confirmation's action was cut off. The body now scrolls. Checked at
  844 x 390: the dialog spans y 24-366 and "Reparse" is reachable and clickable.

## Dropped

- 5 clean-code suggestions with no failure today (hard-coded "20 files", "Two uploads", "50 MB",
  the body-limit sum, `frozenset({DEAD})`): the numbers match the code now; they are drift risks.
- 3 naming or duplication suggestions (`SUMMARY_MODEL_PROVIDER`, the PdfWriter-to-bytes steps, the
  invalidation pair, `isRateLimited`): no defect.
- "Uploading" / "Loading" without an ellipsis: typography nit.
- Lane 4's hover states: the canvas draws none; a matter of design.

## Open (for a person)

- `NoticeProvider.tsx:15` - a reparse, retry or delete answered `409` or `404` shows nothing (the
  confirm dialog has closed); a `429 model_budget_exhausted` on reparse or retry shows the upload
  rate banner with a 60 s countdown. Needs copy for a generic error notice.
- `Notices.tsx:12` - the countdown sits inside `role="status"` and is read out every second.
- `MoreMenu.tsx:43` - menu roles without arrow-key behavior; add it or drop the roles.
- `ReadyBody.tsx:18` - one page-1 request per ready card (up to 20 per feed page), and
  `useDocumentActions.ts:14` / `useUploadFlow.ts:60` invalidate every `['documents']` query. A
  `first_page_preview` on the document would change the API contract.
- `frontend/src/shared/constants/messages.ts:13` - the `max_deliveries` copy says "kept timing out"
  for any repeated failure (already parked with "6 tries").
- Not reported by lane 2 as defects: a budget release that crosses UTC midnight lowers the next day;
  an upload past the in-flight counter's 120 s TTL can free another upload's slot.
- Lane 4 reproduced its two dialog findings by injecting this repo's CSS into a tab of another local
  app (port 5173), not this repo's page; the fixes above were checked on this repo's page.

## Checks after the applied fixes

- Backend: `ruff check`, `ruff format --check`, `mypy` (145 files), `lint-imports` (3 contracts
  kept): clean. `scripts/coverage-gate.sh`: 231 passed, total coverage 96.31%.
- Frontend: `npm run lint`, `npm run typecheck`: clean. `vitest`: 5 passed. `npm run e2e` (6
  projects, rebuilt e2e stack): 156 passed.
- These fixes are a code commit after screens round 2, so the tlc-spec-lean gate now reports the
  screens as not judged at HEAD and `proofs.md` as written at 4aa581f. That goes to the user.
