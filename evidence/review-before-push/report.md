# Review before push: 945baf5..b0ce828 (whole application)

The user asked for every review again over all application code, with the judge deciding what to
fix ("run all the reviews, use a judge to see what we need"). `scripts/review-before-push.sh
945baf5 HEAD` printed the 6 lanes (113, 308, 296, 55, 296, 296 files) and the judge. Each lane ran
as a read-only sub-agent over its own file list; the judge (`code-polish --review`) ran in the
build session against the bar the script printed. This is not a pass: a person confirms each
applied fix.

| Lane | Skill | Findings |
| --- | --- | --- |
| 1 Frontend | typescript-react-reviewer | 8 |
| 2 Backend | python-anti-patterns, solid | 6 |
| 3 Security | security-review | 0 |
| 4 UX, UI | web-design-guidelines | 7 |
| 5 Clean code | clean-code (suggest only) | 15 |
| 6 Performance | performance-optimization | 3 |

## Applied (file and line cited, failure shown, no public contract changed)

Each has a test that fails on the old code unless marked.

- **Lanes 1+5** `frontend/src/pages/UploadPage/hooks/useSession.ts:8` - a `429` on `POST /sessions`
  (21 new sessions a minute from one address) showed the upload-limit copy and the page never
  asked again. Now it waits `Retry-After` and retries until it gets a session. Test:
  `useSession.test.tsx` "waits out a 429 on a new session for Retry-After ...".
- **Lane 1** `useReportError.ts:9` - the offline banner stayed after the API came back. A read
  that succeeds again clears it. Test: `useReportError.test.tsx`.
- **Lane 1** `useActiveDocuments.ts:26` - on "All" a card kept "Queued" while its story said
  "Processing": the feed refetched only when a document left the active list. It now also
  refetches on a status change. Test: `useActiveDocuments.test.tsx` "... moves from queued to
  processing".
- **Lane 1** `useUploadFlow.ts:48` - closing the upload dialog mid-request let the late answer
  write a stale error into the reset dialog. A batch from before the reset is ignored. Test:
  `useUploadFlow.test.tsx`.
- **Lanes 1+5** `shared/api/queryKeys.ts:10` - the pages sheet could flash the old parser's pages
  after a reparse; `pages` is keyed by `updated_at` like `firstPage`. Test:
  `refreshDocuments.test.ts` covers the key list; the flash itself is not tested.
- **Lanes 1+5** `shared/hooks/useCopied.ts:12` - a refused clipboard left an unhandled rejection
  and no feedback; it now says "Couldn't copy" for 2 s. Test: `useCopied.test.ts`.
- **Lane 6** `useConfirmFlow.ts:43`, `useUploadFlow.ts:60` - every action or upload refetched page 1
  of every ready card that had loaded it (100 cards, 100 requests). `refreshDocuments` leaves the
  page-1 previews alone. Test: `refreshDocuments.test.ts`.
- **Lane 4** `PagesSheet.tsx:50` - with 50 pages or fewer a keyboard user could not scroll the
  sheet (Close was its only focusable). The body is a focusable, labelled region. Test: e2e
  "the pages sheet scrolls by keyboard ..." (fails without the fix).
- **Lane 4** `MoreMenu.tsx:39` - a dialog opened from "..." gave focus back to `<body>`. Focus
  moves to "..." before the dialog opens. Test: the same e2e (checked on the new code only; lane
  4 reproduced the old behaviour in the browser).
- **Lane 2** `controllers/schemas/query_params.py:11` - `limit=²` or a 5,000-digit value answered
  `500`; now `422`. Test: `test_bad_pages_limit_is_422`.
- **Lane 2** `rate_limit/redis_sliding_window.py:48` - releasing an in-flight slot was `DECR` then
  `DEL` in two round trips, so a concurrent acquire could lose its count (3 uploads against a cap
  of 2). Release is one Lua script (`in_flight_release.lua`). Test:
  `test_in_flight_counter.py` pins the counting; the race itself is not reproduced.
- **Lane 2** `use_cases/rerun_documents.py:31` - a reparse or retry whose `restart_run` failed
  kept its reserved model pages. They are released and the error re-raised. Test:
  `test_rerun_budget.py`.
- **Lane 2** `models/retry_policy.py:39` - `Retry-After` was uncapped, so one far-off header could
  park a worker for an hour. It is capped at the backoff cap (60 s) and still a floor below it.
  Test: `test_retry_after_is_capped_like_the_backoff`.

## Dropped (19)

- **Lane 5, 12 items:** no failure today. They are drift risks, dead code or naming:
  - DOMAIN_STATUS for a future error class;
  - the "Two uploads", 20 files, 50 MB and 1,000 pages literals;
  - unused `is_final`, `with_status`, `FINAL_STATUSES`, `Job.object_key`, `isRateLimited`,
    `isActive`, `MAX_PAGES`;
  - the failure-cause string keys;
  - the `pypdf_parse_timeout_s` name;
  - two duplicated mappings;
  - the literal feed key;
  - the ignored `finalize` result, which only affects a log line.
- **Lane 1, missing error boundary:** no status or input that throws today.
- **Lane 2, Redis client retries re-running scripts:** low confidence; it needs a reply lost after
  the script ran.
- **Lane 5, 3 items:** duplicates of lane 1 items applied above.

## Open (for a person)

- **Lane 2 `s3_object_storage.py:59`, `process_document.py:107`.** The PDF expires 7 days after it
  was put, but the record's TTL restarts on each change.
  - **Failure:** a reparse on day 8 of a document reparsed on day 5 fails 5 times, then ends
    `max_deliveries` "an unexpected error".
  - **Why Open:** the fix adds an error code (`source_expired`), which changes the API contract
    (door 3). The bucket lifecycle on SeaweedFS is not verified either.
- **Lane 6 `upload_documents.py:85`.** The 3-files-in-parallel semaphore is per request, so many
  sessions can hold about 3 GiB of read files waiting for 4 inspection slots.
  - **Why Open:** a per-process semaphore changes cross-request fairness, and the cost was not
    measured.
- **Lane 6 `useActiveDocuments.ts:30`.** Refetching the infinite feed re-requests every loaded
  page.
  - **Why Open:** `maxPages` or a first-page-only refetch changes how older pages behave; that is
    a choice for a person.
- **Lane 1 `useStoryScroll.ts:19`.** Tapping the story of a document outside the first 20 cards
  does nothing, then jumps later.
  - **Why Open:** the fix (page until found, or clear the target) needs more than 20 documents to
    verify.
- **Lane 4.** Focus after a confirmed action that removes its opener, focus after a story tap,
  scroll padding under the phone bars, focus in the upload dialog after remove or unlock, and
  summary heading levels.
  - **Why Open:** each is unverified in the browser or changes what a screen draws.

## Also changed

- `scripts/proofs/e2e-stack.sh` clears the e2e stack's `budget:model_pages:*` counters each time
  it brings the stack up, so repeated runs in one UTC day never end in `429
  model_budget_exhausted` (AD-051). The limit stays 3,000, as the pictures draw.
  `playwright.captures.config.ts` uses the same global setup, which also restores the 1.5 s stub
  delay the stories frames need. Checked: a counter set to 2,999 is gone after the script runs.

## Earlier run: 945baf5..4aa581f

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

### Applied (the judge kept these: file and line cited, failure shown, no public contract changed)

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

### Dropped

- 5 clean-code suggestions with no failure today (hard-coded "20 files", "Two uploads", "50 MB",
  the body-limit sum, `frozenset({DEAD})`): the numbers match the code now; they are drift risks.
- 3 naming or duplication suggestions (`SUMMARY_MODEL_PROVIDER`, the PdfWriter-to-bytes steps, the
  invalidation pair, `isRateLimited`): no defect.
- "Uploading" / "Loading" without an ellipsis: typography nit.
- Lane 4's hover states: the canvas draws none; a matter of design.

### Open (for a person)

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

### Checks after the applied fixes

- Backend: `ruff check`, `ruff format --check`, `mypy` (145 files), `lint-imports` (3 contracts
  kept): clean. `scripts/coverage-gate.sh`: 231 passed, total coverage 96.31%.
- Frontend: `npm run lint`, `npm run typecheck`: clean. `vitest`: 5 passed. `npm run e2e` (6
  projects, rebuilt e2e stack): 156 passed.
- These fixes are a code commit after screens round 2, so the tlc-spec-lean gate now reports the
  screens as not judged at HEAD and `proofs.md` as written at 4aa581f. That goes to the user.
