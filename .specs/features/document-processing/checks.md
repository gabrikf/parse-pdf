# Document processing checks

Build: `cd backend && ../.venv/bin/ruff check . && ../.venv/bin/ruff format --check . && ../.venv/bin/mypy && ../.venv/bin/lint-imports`; `npm --prefix frontend run lint`; `npm --prefix frontend run typecheck`; `npm --prefix frontend run build`
Run backend: `docker compose -f compose.test.yaml up -d --wait >/dev/null 2>&1 && cd backend && ../.venv/bin/python -m pytest -v`
Run web: `npm --prefix frontend run test -- --reporter=verbose`
Run e2e: `npm --prefix frontend run e2e -- --reporter=list`
Plan: `.specs/features/document-processing/plan.md`

81 checks in 7 slices · 13 one-way doors · 0 open, of which 0 block

Backend integration tests run against the real Redis and SeaweedFS of `compose.test.yaml`, with
OpenRouter replaced by a fake `ChatModel`, respx, or the local stub (`backend/stubs/`). The
concurrency, restart and clean-checkout proofs run against Compose stacks; their output is saved
in `evidence/concurrency/` and `evidence/compose/`. No proof calls the real OpenRouter.

## Checks

### S1 - Upload with PyPDF through the Redis Streams queue, served concurrently

**C1** - A clean checkout with `.env` from `.env.example` and `SESSION_SECRET` set brings `redis`, `storage`, `api`, `worker`, `web` to `healthy`, `api` and `worker` waiting on `redis` and `storage` with `service_healthy` (AC 1)
Proof: `scripts/compose-check.sh`

**C2** - `SESSION_SECRET` unset or 31 bytes stops the API at start naming `SESSION_SECRET`; 32 bytes starts (AC 2)
Proof: run backend | test_unset_secret_is_refused PASSED
Proof: run backend | test_31_byte_secret_is_refused PASSED
Proof: run backend | test_32_byte_secret_starts PASSED
Proof: run backend | test_serve_exits_1_naming_the_variable PASSED

**C3** - `POST /api/v1/sessions` returns `201` with an `HttpOnly`, `SameSite=Lax`, 604,800 s `pp_session` cookie and `data.session_id`; again with the cookie, `200` and the same id (AC 3)
Proof: run backend | test_new_session_sets_cookie_and_reuse_returns_same_id PASSED

**C4** - Every `/api/v1/documents` route answers `401 session_required` with no cookie, a tampered signature, `alg: none` or a token expired 1 s ago, and accepts a valid Bearer (AC 4)
Proof: run backend | test_document_routes_without_session_are_401 PASSED
Proof: run backend | test_invalid_tokens_are_401 PASSED
Proof: run backend | test_valid_bearer_is_accepted PASSED

**C5** - 1 to 20 valid PDFs with `parser=pypdf` return `202` with one `queued` item per file in upload order, each stored at `documents/{id}.pdf` with exactly one stream entry `{document_id, object_key, run_id}` (AC 5)
Proof: run backend | test_upload_queues_each_file_in_order_and_stores_it PASSED
Proof: run backend | test_20_files_are_accepted PASSED

**C6** - `parser` omitted, `""`, `"PyPDF"` or `"gpt5mini"` returns `422 invalid_parser` with the 3 allowed values and stores nothing; `"pypdf"` returns `202` (AC 6)
Proof: run backend | test_unknown_parser_is_422_and_stores_nothing PASSED

**C7** - 0 files return `422 no_files`; 21 files return `422 too_many_files` with 0 objects stored; 20 return `202` (AC 7)
Proof: run backend | test_no_files_is_422 PASSED
Proof: run backend | test_21_files_are_422_and_store_nothing PASSED

**C8** - A PNG named `scan.pdf` is `not_pdf`, `%PDF-` after byte 1,024 is `not_pdf`, 0 bytes is `empty`, garbage after the magic is `unreadable_pdf`; 1 bad + 2 good is `202` with 2 documents and 1 rejected; 3 bad is `422 all_files_rejected` with 3 rejected; a PDF named `report.txt` is accepted (AC 8)
Proof: run backend | test_bad_files_are_rejected_beside_good_ones PASSED
Proof: run backend | test_signature_after_first_1024_bytes_is_not_pdf PASSED
Proof: run backend | test_all_bad_files_is_422_all_files_rejected PASSED

**C9** - 52,428,800 bytes and 1000 pages are `queued`; 52,428,801 bytes and 1001 pages are `too_large` with no object and no stream entry (AC 9)
Proof: run backend | test_size_boundary PASSED
Proof: run backend | test_page_boundary PASSED

**C10** - A body past 1,074,790,400 bytes is cut off with `413 request_too_large`, whatever `Content-Length` claims (AC 10)
Proof: run backend | test_body_over_limit_is_413_whatever_content_length_says PASSED
Proof: run backend | test_declared_length_over_limit_is_413 PASSED

**C11** - A `pypdf` job ends `ready` and its pages read back as `{number, content, format: "text"}` in page order (AC 11)
Proof: run backend | test_pypdf_job_ends_ready_with_text_pages_in_order PASSED

**C12** - 3 blank pages end `no_text` with a hint naming `gemini-3.1-flash-lite`; 1 character on page 2 of 3 does not (AC 12)
Proof: run backend | test_all_blank_pages_end_no_text_with_gemini_hint PASSED
Proof: run backend | test_one_character_on_page_2_of_3_is_not_no_text PASSED

**C13** - `queued`, `processing`, `no_text`, `too_large` and `dead` documents return `summary: null` and `409 not_ready` on pages (AC 13)
Proof: run backend | test_not_ready_document_hides_summary_and_pages PASSED
Proof: run backend | test_ready_document_shows_summary_and_pages_in_order PASSED

**C14** - Another session's document answers `404 document_not_found` on read, pages, reparse, requeue and delete, like a missing id (AC 14)
Proof: run backend | test_foreign_document_is_404_like_a_missing_one PASSED

**C15** - The feed holds only the session's documents, newest first, 20 by default, at most 50; 45 documents at `limit=20` page 20 + 20 + 5 with no cursor on the third; `limit=0`, `51`, `abc` are `422 invalid_limit` (AC 15)
Proof: run backend | test_feed_shows_only_own_documents PASSED
Proof: run backend | test_feed_pages_newest_first_with_cursor PASSED
Proof: run backend | test_feed_default_limit_is_20 PASSED
Proof: run backend | test_limit_50_is_accepted PASSED
Proof: run backend | test_bad_limit_is_422 PASSED
Proof: run backend | test_bad_cursor_is_422 PASSED

**C16** - 1 queued + 2 ready + 1 dead: `state=parsed` gives the 2 ready, `failed` the dead one, `active` the queued one, omitted all 4; `state=` and `state=final` are `422 invalid_state` (AC 16)
Proof: run backend | test_feed_states_filter_groups_and_count PASSED
Proof: run backend | test_feed_parsed_holds_no_text_and_failed_holds_too_large PASSED
Proof: run backend | test_unknown_state_is_422 PASSED

**C17** - An 11th upload in 60 s is `429 rate_limited` with whole-second `Retry-After`; a 3rd in-flight upload is `429 too_many_uploads_in_progress`; a 21st session from one IP in 60 s is `429 rate_limited` (AC 17)
Proof: run backend | test_11th_upload_in_60s_is_429_rate_limited PASSED
Proof: run backend | test_third_upload_in_flight_is_429 PASSED
Proof: run backend | test_21st_session_from_one_ip_within_60s_is_429 PASSED

**C18** - `Origin` equal to `PAGE_ORIGIN` is echoed with credentials; any other origin gets no `Access-Control-Allow-Origin`; never `*` (AC 18)
Proof: run backend | test_cors_echoes_page_origin_with_credentials PASSED
Proof: run backend | test_cors_sends_nothing_for_other_origins PASSED

**C19** - The `Preset.BASIC` headers are on a `200`, a `404`, a `422` and a `500`, header by header (AC 19)
Proof: run backend | test_basic_preset_headers_on_200_404_422_500 PASSED

**C20** - Every JSON answer is `{data, error, meta}` with `X-Request-ID`; an unexpected exception is `500 internal_error` with no exception text (AC 20)
Proof: run backend | test_envelope_and_request_id_on_success_and_error PASSED
Proof: run backend | test_unknown_route_is_an_envelope PASSED
Proof: run backend | test_500_is_an_envelope_without_exception_text PASSED

**C21** - `/health/ready` is `200` when Redis and the bucket answer and `503 not_ready` naming each failing check otherwise; `/health/live` is `200` (AC 21)
Proof: run backend | test_ready_is_200_when_redis_and_bucket_answer PASSED
Proof: run backend | test_ready_is_503_naming_each_failing_check PASSED
Proof: run backend | test_live_is_200 PASSED

**C22** - With 3 workers, 5,000 `GET /api/v1/documents` at concurrency 200 are all `200`, and 50 sessions uploading at once all get `202`, reach `ready` and show `deliveries: 1`; output in `evidence/concurrency/` (AC 22)
Proof: `scripts/proofs/concurrency.sh`

**C23** - The upload answers `202 queued` before any worker reads the entry, and `/health/live` keeps answering under 0.5 s during a 1000-page upload (AC 23)
Proof: run backend | test_upload_returns_queued_before_any_worker_runs PASSED
Proof: run backend | test_live_answers_during_a_1000_page_upload PASSED

**C24** - A Redis restart with 5 documents `queued` ends with all 5 `ready`, and the first API request after Redis is back is not a `5xx` (AC 24)
Proof: `scripts/proofs/redis-restart.sh`

**C25** - Every `doc:*` and `session:*` key has a TTL of 604,800 s, refreshed on a status change; the bucket expires objects after 7 days (AC 25)
Proof: run backend | test_every_doc_and_session_key_gets_a_week PASSED
Proof: run backend | test_a_status_change_refreshes_the_ttl PASSED
Proof: run backend | test_bucket_expires_objects_after_7_days PASSED

**C26** - `../../etc/passwd.pdf` is stored as filename `passwd.pdf` under key `documents/{uuid}.pdf`; control characters are dropped and the name is cut to 255 characters (AC 26)
Proof: run backend | test_filename_is_cleaned_and_never_the_key PASSED

### S2 - One summary per file with gemini-3.1-flash-lite, guarded and rate-limit safe

**C27** - The summary comes from `google/gemini-3.1-flash-lite` and `ready` is set only with it stored; the prompt asks for markdown, a 3-6 sentence overview, at most 5 bullet key points, in the document's language (AC 27)
Proof: run backend | test_ready_is_set_only_with_the_stored_summary PASSED
Proof: run backend | test_summary_model_is_gemini_and_markdown_rules_are_asked PASSED

**C28** - `" gemini-3.1-flash-lite ”`, `gemini-3.1-flash-lite` and `google/gemini-3.1-flash-lite` all resolve to `google/gemini-3.1-flash-lite` (AC 28)
Proof: run backend | test_brief_model_id_resolves_to_openrouter_id PASSED
Proof: run backend | test_settings_normalize_summary_model_id PASSED

**C29** - 300,000 characters take 1 summary call; 300,001 take 3 (2 map + 1 reduce) (AC 29)
Proof: run backend | test_300000_characters_take_one_summary_call PASSED
Proof: run backend | test_300001_characters_take_two_maps_and_one_reduce PASSED

**C30** - Document text goes only in the user message inside `<document>` delimiters, with a system message saying it is data; a closing delimiter in the text is escaped (AC 30)
Proof: run backend | test_document_text_only_in_user_message_inside_delimiters PASSED
Proof: run backend | test_wrap_document_escapes_the_closing_delimiter PASSED

**C31** - Llama Guard checks every input piece before any summary call and the final summary; `unsafe` input or output ends `dead` `guardrail_rejected` with no retry and no summary call for rejected input (AC 31)
Proof: run backend | test_every_input_piece_and_the_summary_are_guarded PASSED
Proof: run backend | test_all_input_is_guarded_before_the_first_summary_call PASSED
Proof: run backend | test_unsafe_input_is_rejected_without_a_summary_call PASSED
Proof: run backend | test_unsafe_summary_is_rejected PASSED
Proof: run backend | test_unsafe_input_ends_dead_guardrail_rejected_without_a_summary_call PASSED

**C32** - 429, 5xx and a 60 s timeout retry up to 6 attempts (1 s base, x2, 60 s cap, full jitter, `Retry-After` as a floor); 429, 429, 200 ends after 3 calls; `Retry-After: 7` waits >= 7 s; 6 x 429 leaves the job pending and `processing`, and the next delivery counts `deliveries` 2 (AC 32)
Proof: run backend | test_429_429_200_returns_after_three_calls PASSED
Proof: run backend | test_retry_after_7_waits_at_least_7s PASSED
Proof: run backend | test_six_429s_raise_transient PASSED
Proof: run backend | test_5xx_is_retried PASSED
Proof: run backend | test_timeout_is_retried PASSED
Proof: run backend | test_a_call_past_the_deadline_is_a_retryable_timeout PASSED
Proof: run backend | test_delays_double_from_1s_and_cap_at_60s PASSED
Proof: run backend | test_full_jitter_draws_between_zero_and_the_backoff PASSED
Proof: run backend | test_retries_run_out_and_the_entry_stays_pending_for_redelivery PASSED

**C33** - 400, 401, 403, 404 end `dead` `provider_rejected`, 402 `provider_out_of_credits`, an empty key `provider_not_configured`, none retried (AC 33)
Proof: run backend | test_permanent_statuses_are_not_retried PASSED
Proof: run backend | test_empty_key_is_not_configured_with_no_call PASSED
Proof: run backend | test_permanent_provider_errors_end_dead_without_retry PASSED

**C34** - 40 calls from 2 workers on one Redis with a fake clock: 30 start in the first 60 s, 10 after; 1 at a time per worker (AC 34)
Proof: run backend | test_40_calls_from_two_workers_start_30_then_10_after_60s PASSED
Proof: run backend | test_one_call_at_a_time_per_worker PASSED

### S3 - Crash recovery that is shown

**C35** - A real worker process killed with SIGKILL mid-job has its entry claimed by another worker after `JOB_CLAIM_IDLE_MS` idle, and the document ends `ready` with `deliveries` 2 (AC 35)
Proof: run backend | test_sigkilled_worker_job_is_reclaimed_and_ends_ready PASSED
Proof: run backend | test_idle_entry_is_reclaimed_by_another_worker PASSED

**C36** - A job running 3 x `JOB_CLAIM_IDLE_MS` with claim refresh stays on one worker (`deliveries: 1`) (AC 36)
Proof: run backend | test_claim_refresh_keeps_a_long_job_on_one_worker PASSED

**C37** - The 6th delivery ends `dead` `max_deliveries` with 0 parser or model calls, copies `{document_id, run_id, error_code, deliveries}` to `docs:dead` and acks; the 5th is processed (AC 37)
Proof: run backend | test_sixth_delivery_is_dead_letter_with_no_calls PASSED

**C38** - A redelivered entry whose run is already final is acked with 0 parser and 0 model calls (AC 38)
Proof: run backend | test_redelivered_final_run_is_acked_with_no_calls PASSED

**C39** - An entry with an old `run_id` or a deleted document is acked and dropped with 0 calls (AC 39)
Proof: run backend | test_stale_run_and_deleted_document_are_dropped PASSED

**C40** - On SIGTERM a worker stops reading and finishes the running job; a job still running at the grace leaves its entry pending; a real worker exits 0 on SIGTERM (AC 40)
Proof: run backend | test_stop_signal_lets_the_running_job_finish PASSED
Proof: run backend | test_job_past_the_grace_stays_pending_for_reclaim PASSED
Proof: run backend | test_sigterm_exits_cleanly_and_heartbeat_goes_stale PASSED

**C41** - A heartbeat 29 s old is healthy, 31 s old, missing or garbled is unhealthy; the healthcheck command exits 0 and 1 accordingly (AC 41)
Proof: run backend | test_29s_old_is_fresh_and_31s_old_is_stale PASSED
Proof: run backend | test_missing_or_garbled_heartbeat_is_stale PASSED
Proof: run backend | test_main_exit_codes PASSED

### S4 - Gemini markdown and GPT-5 Mini OCR parsers, chunked and budgeted

**C42** - Model parsers send 10-page chunks as a `file` part with the `native` engine and a JSON-schema response and store `markdown` pages; 23 pages take 10, 10 and 3; 10 pages take 1 call (AC 42)
Proof: run backend | test_23_pages_take_calls_of_10_10_3_and_return_markdown_pages PASSED
Proof: run backend | test_10_pages_take_one_call PASSED
Proof: run backend | test_request_sends_a_pdf_file_part_native_engine_and_json_schema PASSED
Proof: run backend | test_split_23_pages_into_10_10_3 PASSED

**C43** - A chunk answer that misses, repeats or adds a page is retried up to 2 more times, then `dead` `model_output_invalid` (AC 43)
Proof: run backend | test_invalid_answer_is_retried_twice_then_dead PASSED
Proof: run backend | test_one_invalid_answer_then_valid_succeeds PASSED

**C44** - 3 chunks with a crash after chunk 2: the resumed job sends only chunk 3 (AC 44)
Proof: run backend | test_resumed_job_sends_only_missing_chunks PASSED

**C45** - 2,990 used + 10 pages is accepted (3,000); + 11 pages is `model_budget_exhausted` in `rejected[]`; a reparse past it is `429`; the next UTC day starts at 0; each summary adds 1; `pypdf` is never refused (AC 45)
Proof: run backend | test_2990_used_plus_10_pages_is_accepted_and_reaches_3000 PASSED
Proof: run backend | test_2990_used_plus_11_pages_is_refused_and_not_stored PASSED
Proof: run backend | test_reparse_past_the_budget_is_429 PASSED
Proof: run backend | test_next_utc_day_starts_at_0 PASSED
Proof: run backend | test_each_summary_adds_one_budget_page PASSED
Proof: run backend | test_pypdf_is_never_refused_by_the_budget PASSED

**C46** - A scanned (image-only) PDF parsed by `gpt-5-mini` and by `gemini-3.1-flash-lite` ends `ready` with non-empty markdown on every page; record in `evidence/model-parsers/` (AC 46)
Proof: run backend | test_scanned_pdf_reaches_ready_with_markdown_pages[gemini-3.1-flash-lite] PASSED
Proof: run backend | test_scanned_pdf_reaches_ready_with_markdown_pages[gpt-5-mini] PASSED

### S5 - Reparse, requeue, delete, and password-protected PDFs

**C47** - Reparse from `ready`, `no_text` or `dead` returns `202`, sets `queued` with a new `run_id`, clears pages, chunks and summary and adds exactly one entry; 2 concurrent reparses give one `202` and one `409 document_busy` (AC 47)
Proof: run backend | test_reparse_a_final_document_queues_a_new_run_with_cleared_results PASSED
Proof: run backend | test_two_concurrent_reparses_give_one_202_and_one_409 PASSED
Proof: run backend | test_reparse_with_a_bad_parser_is_422 PASSED

**C48** - Reparse or requeue of `queued` or `processing` is `409 document_busy`; reparse of `too_large` is `409 not_reparsable` (AC 48)
Proof: run backend | test_busy_documents_refuse_reparse_and_requeue PASSED
Proof: run backend | test_reparse_too_large_is_not_reparsable PASSED
Proof: run backend | test_each_status_allows_or_refuses_each_action PASSED

**C49** - Requeue of `dead` returns `202` with the same parser; of `ready`, `no_text` or `too_large`, `409 not_dead` (AC 49)
Proof: run backend | test_requeue_a_dead_document_keeps_its_parser PASSED
Proof: run backend | test_requeue_a_document_that_is_not_dead_is_409 PASSED

**C50** - Delete returns `200` `{id, deleted: true}` and removes record, pages, chunks, every feed entry and the object; `processing` is `409 document_busy` (AC 50)
Proof: run backend | test_delete_removes_record_pages_chunks_feed_and_object PASSED
Proof: run backend | test_delete_a_processing_document_is_409 PASSED
Proof: run backend | test_delete_a_queued_document_is_200 PASSED

**C51** - An encrypted PDF that opens with an empty password is accepted like any PDF (AC 51)
Proof: run backend | test_empty_password_pdf_is_accepted_like_any_pdf PASSED
Proof: run backend | test_empty_password_pdf_opens_and_is_decrypted PASSED

**C52** - A locked PDF with no or empty password is `password_required`, with a wrong one `wrong_password`, and nothing is stored (AC 52)
Proof: run backend | test_missing_or_wrong_password_is_rejected_and_nothing_stored PASSED
Proof: run backend | test_password_needed_wrong_and_right PASSED

**C53** - The right password applies to every file of the request; the stored object is decrypted; the password literal is in no response, no Redis `DUMP` of any key, no stored object and no log line (AC 53)
Proof: run backend | test_right_password_stores_decrypted_bytes_and_never_the_password PASSED

### S6 - Upload page on phone, tablet and desktop

**C54** - A first visit creates the session and shows the empty-feed message and the upload form, as `captures/PhoneEmpty.png` draws; documents show newest first (AC 54)
Proof: run e2e | ✓ first visit creates a session and shows the empty feed
Proof: browser - reach the empty feed at 375 x 812, save `captures/PhoneEmpty.running.png`

**C55** - The parser select offers exactly `pypdf`, `gemini-3.1-flash-lite`, `gpt-5-mini`, `pypdf` selected by default (AC 55)
Proof: run e2e | ✓ the parser select offers exactly three parsers with pypdf selected

**C56** - Files added by picker, drag-and-drop and paste are listed with name and size; a 21st shows "Up to 20 files per upload" and is not added (AC 56)
Proof: run e2e | ✓ files added by picker, drop and paste are listed with name and size
Proof: run e2e | ✓ a 21st file shows up to 20 files per upload

**C57** - Submit sends one upload request, shows each accepted file in the feed with its status and each rejected file inline with its reason, as `captures/DesktopUpload.png` draws (AC 57)
Proof: run e2e | ✓ upload 3 samples by picker reaches the parsed feed
Proof: run e2e | ✓ refused files show their reason inline
Proof: browser - submit 3 files with 1 refused at 1280 x 1240, save `captures/DesktopUpload.running.png`

**C58** - A `password_required` or `wrong_password` file shows a password field; submitting it re-sends only that file with the password (AC 58)
Proof: run e2e | ✓ a locked file asks for its password and re-sends only that file

**C59** - While any document is active the page polls `state=active` every 2,000 ms, refetches the feed when one leaves, and stops when the list is empty (AC 59)
Proof: run web | ✓ polls the active list every 2000 ms and stops when it is empty
Proof: run web | ✓ refetches the feed when a document leaves the active list

**C60** - A `ready` document shows its summary and pages 50 at a time with a control for the next 50; `<script>alert(1)</script>` shows as literal text, as `captures/PhonePages.png` draws (AC 60)
Proof: run e2e | ✓ the pages sheet shows 50 pages and loads the next 50
Proof: run web | ✓ markdown shows raw html as literal text
Proof: browser - open the pages sheet of a ready document at 375 x 812 dark, save `captures/PhonePages.running.png`

**C61** - A `no_text` document shows its hint and an action to reparse it with `gemini-3.1-flash-lite` (AC 61)
Proof: run e2e | ✓ a no_text card shows its hint and reparses with gemini

**C62** - Reparse, requeue and delete each ask for confirmation naming the file and the action; cancel sends nothing; confirm sends and shows the new status or removes the card, as `captures/PhoneConfirm.png` draws (AC 62)
Proof: run e2e | ✓ reparse with another parser asks first and cancel sends nothing
Proof: run e2e | ✓ delete forever removes the card and it stays gone after reload
Proof: browser - open the reparse confirmation at 375 x 812, save `captures/PhoneConfirm.running.png`

**C63** - An unreachable API shows an error with a retry control; a `429` shows the wait in seconds from `Retry-After` (AC 63)
Proof: run web | ✓ an unreachable api shows an error with a retry control
Proof: run e2e | ✓ a rate-limited upload shows the wait in seconds

**C64** - At 375, 768 and 1280 px there is no horizontal scroll, every control is reachable by keyboard with a visible focus ring, dialogs close on Escape and keep focus inside, and touch hit areas are at least 44 x 44 px (AC 64)
Proof: run e2e | ✓ no horizontal scroll and touch targets are at least 44 px
Proof: run e2e | ✓ keyboard-only upload and confirm with a visible focus ring
Proof: run e2e | ✓ dialogs close on escape and keep focus inside

**C65** - The page sends requests only to its own origin under `/api/v1/`, never to OpenRouter, Redis or the bucket; record in `evidence/upload-page/` (AC 65)
Proof: run e2e | ✓ the page calls only its own origin under /api/v1/

**C66** - Every label, message and button is English in sentence case (AC 66)
Proof: run e2e | ✓ every visible label and button is in sentence case

**C67** - The page is an Instagram-style feed in one purple primary (`#6D28D9` light, `#A78BFA` dark), Newsreader and Schibsted Grotesk, Lucide outline icons, hairlines, no shadows or gradients, as `captures/Main.png`, `captures/PhoneLight.png` and `captures/Tablet.png` draw (AC 67)
Proof: run e2e | ✓ the primary color, fonts and no shadows or gradients
Proof: browser - reach the parsed feed at 1280 x 1240 light, save `captures/Main.running.png`
Proof: browser - reach the parsed feed at 375 x 812 light, save `captures/PhoneLight.running.png`
Proof: browser - reach the parsed feed at 768 x 1024 light, save `captures/Tablet.running.png`

**C68** - The first load follows the system scheme; the toggle switches light and dark and is kept on the next visit; text and controls keep 4.5:1 contrast in both themes, as `captures/DesktopDark.png` and `captures/PhoneDark.png` draw (AC 68)
Proof: run e2e | ✓ the theme follows the system and the toggle is remembered
Proof: run e2e | ✓ text and controls keep 4.5 to 1 contrast
Proof: browser - reach the parsed feed at 1280 x 1240 dark, save `captures/DesktopDark.running.png`
Proof: browser - reach the parsed feed at 375 x 812 dark, save `captures/PhoneDark.running.png`

**C69** - Active documents show in the stories row with a status ring; tapping one scrolls to its card; a final document leaves the row; the row hides when empty (AC 69)
Proof: run e2e | ✓ the stories row shows active documents and hides when empty

**C70** - From 1024 px the page shows the icon rail, the centered feed and the right rail with the parser guide and today's budget from `GET /api/v1/budget`; below 768 px a bottom tab bar (AC 70)
Proof: run e2e | ✓ wide screens show both rails with the budget and phones a tab bar

**C71** - "Copy summary" copies the summary markdown and shows "Copied" for 2 s (AC 71)
Proof: run e2e | ✓ copy summary copies the markdown and shows copied

**C72** - The feed opens on "Parsed" (`state=parsed`); "Failed" shows `dead` and `too_large`; "All" shows every document newest first; each chip shows its count; chips never filter the stories row; the choice resets on each visit, as `captures/PhoneFailed.png` draws (AC 72)
Proof: run e2e | ✓ parsed, failed and all chips filter the feed with counts
Proof: browser - select Failed at 375 x 812, save `captures/PhoneFailed.running.png`

**C73** - A `dead` card offers "Retry", "Reparse with another parser" and "Delete forever"; a `too_large` card only "Delete forever"; each opens its own confirmation naming the file; "Delete forever" says it cannot be undone in the danger color; a confirmed retry moves the card to the stories row as queued, as `captures/PhoneDelete.png` draws (AC 73)
Proof: run e2e | ✓ retry a dead document moves it to the stories row as queued
Proof: run e2e | ✓ a too_large card offers only delete forever
Proof: browser - open the delete forever confirmation at 375 x 812, save `captures/PhoneDelete.running.png`

### S7 - Demo kit, README, delivery zip

**C74** - The README has every section criterion 74 lists, in order (AC 74)
Proof: `python3 scripts/proofs/check_readme.py sections`

**C75** - "How I worked" describes, in order, the harness, the brief, planning with `tlc-spec-lean`, designing with `frontend-blueprint`, slice-by-slice build, the fresh-subagent review and `/review-before-push` (AC 75)
Proof: `python3 scripts/proofs/check_readme.py how-i-worked`

**C76** - The README states the key holds $5, the daily budget is 3,000 model pages, and what a reviewer sees when credit runs out (`provider_out_of_credits`) (AC 76)
Proof: `python3 scripts/proofs/check_readme.py budget`

**C77** - `docs/postman/parse-pdf.postman_collection.json` covers all 11 routes of `Surface`, and `samples/` holds a text PDF, a scanned PDF, an encrypted PDF (password in the README) and a PDF over 10 pages, each with source and license (AC 77)
Proof: `python3 scripts/proofs/check_readme.py postman-and-samples`

**C78** - The README curl walkthrough, run line by line against the e2e stack, gives the statuses the README shows (AC 78)
Proof: `scripts/proofs/curl-walkthrough.sh`

**C79** - `scripts/package.sh` builds a zip with no `.venv`, `node_modules`, `.env`, `.specs`, `.claude` or `evidence` file (AC 79)
Proof: `scripts/proofs/package-check.sh`

**C80** - The backend passes ruff check and format, `mypy --strict`, `lint-imports` and the 85% line and branch coverage gate with no `app/` module over 200 lines; the frontend passes lint and `tsc --noEmit` (AC 80)
Proof: `scripts/coverage-gate.sh`
Proof: run backend | test_no_app_module_is_over_200_lines PASSED

**C81** - Every Playwright scenario passes in Chromium at 375 x 812, 768 x 1024 and 1280 x 1240, light and dark, against the Compose stack with the e2e override and the OpenRouter stub, `retries: 0`, report and screenshots in `evidence/e2e/` (AC 81)
Proof: `npm --prefix frontend run e2e`

## Coverage

| Set (size) | Member -> proof | Unproven |
| --- | --- | --- |
| `POST /api/v1/sessions` statuses (3) | 201 C3 · 200 C3 · 429 C17 | - |
| `POST /api/v1/documents` statuses (11) | 202 C5 · 422 `invalid_parser` C6 · 422 `no_files` C7 · 422 `too_many_files` C7 · 422 `all_files_rejected` C8 · 413 C10 · 429 `rate_limited` C17 · 429 `too_many_uploads_in_progress` C17 · 401 C4 · `too_large` items C9 · `rejected[]` items C8 | - |
| `GET /api/v1/documents` statuses (5) | 200 C15 · 422 `invalid_limit` C15 · 422 `invalid_cursor` C15 · 422 `invalid_state` C16 · 401 C4 | - |
| `GET /api/v1/documents/{id}` statuses (3) | 200 C11 · 404 C14 · 401 C4 | - |
| `GET /api/v1/documents/{id}/pages` statuses (5) | 200 C11 · 409 C13 · 404 C14 · 422 C15 · 401 C4 | - |
| `POST /api/v1/documents/{id}/reparse` statuses (7) | 202 C47 · 409 `document_busy` C48 · 409 `not_reparsable` C48 · 422 C47 · 429 C45 · 404 C14 · 401 C4 | - |
| `POST /api/v1/documents/{id}/requeue` statuses (5) | 202 C49 · 409 `document_busy` C48 · 409 `not_dead` C49 · 404 C14 · 401 C4 | - |
| `DELETE /api/v1/documents/{id}` statuses (4) | 200 C50 · 409 C50 · 404 C14 · 401 C4 | - |
| `GET /api/v1/budget` statuses (2) | 200 C70 · 401 C4 | - |
| `GET /api/v1/health/live` statuses (1) | 200 C21 | - |
| `GET /api/v1/health/ready` statuses (2) | 200 C21 · 503 C21 | - |
| upload rejection codes (7) | `not_pdf` C8 · `empty` C8 · `unreadable_pdf` C8 · `password_required` C52 · `wrong_password` C52 · `model_budget_exhausted` C45 · `too_large` C9 | - |
| final statuses (4) | `ready` C11 · `no_text` C12 · `too_large` C9 · `dead` C37 | - |
| dead error codes (7) | `max_deliveries` C37 · `guardrail_rejected` C31 · `provider_rejected` C33 · `provider_out_of_credits` C33 · `provider_not_configured` C33 · `model_output_invalid` C43 · `unreadable_pdf` C8 | - |
| parsers (3) | `pypdf` C11 · `gemini-3.1-flash-lite` C46 · `gpt-5-mini` C46 | - |
| feed groups (4) | `parsed` C16 · `failed` C16 · `active` C16 · `all` C16 | - |
| status x action table (18) | C48, table-driven over all 18 cells | - |
| invalid session tokens, AC 4 (5 examples) | none C4 · tampered C4 · `alg: none` C4 · expired C4 · Bearer C4 | - |
| `parser` values, AC 6 (5 examples) | omitted C6 · `""` C6 · `PyPDF` C6 · `gpt5mini` C6 · `pypdf` C6 | - |
| boundaries, AC 7 and 9 (7 examples) | 0 files C7 · 20 files C7 · 21 files C7 · 52,428,800 B C9 · 52,428,801 B C9 · 1000 pages C9 · 1001 pages C9 | - |
| retry examples, AC 32 (3 examples) | 429 429 200 C32 · `Retry-After: 7` C32 · 6 x 429 C32 | - |
| budget examples, AC 45 (3 examples) | 2,990 + 10 C45 · 2,990 + 11 C45 · next UTC day C45 | - |
| summary model id forms, AC 28 (3 examples) | brief literal C28 · bare C28 · prefixed C28 | - |
| startup config: session secret (2 assemblies) | `app/serve.py` entry point C2 · test settings C2 | - |
| startup config: worker wiring (2 assemblies) | `app/worker/main.py` process C35 · in-process `worker_loop` C46 | - |
| source controls: upload page (12) | parser select C55 · file picker C56 · drop zone C56 · paste C56 · upload button C57 · password field C58 · load next 50 C60 · reparse C62 · requeue / Retry C73 · delete forever C62 · theme toggle C68 · Parsed / Failed / All chips C72 | - |
| captures (11) | Main C67 · DesktopDark C68 · DesktopUpload C57 · PhoneLight C67 · PhoneDark C68 · PhoneEmpty C54 · PhonePages C60 · PhoneConfirm C62 · PhoneDelete C73 · PhoneFailed C72 · Tablet C67 | - |
| viewports, AC 81 (6 projects) | 375 light C81 · 375 dark C81 · 768 light C81 · 768 dark C81 · 1280 light C81 · 1280 dark C81 | - |

## Swept

- validation: C6, C7, C8, C9, C10, C15, C16, C26
- failure modes: C32, C33, C43, C24
- idempotency: C38, C39, C44
- authorization: C4, C14, C17
- concurrency: C22, C34, C36, C47
- data lifecycle: C25, C50, C53
- dependency failure: C21, C24, C32, C33
- state transitions: C47, C48, C49, C50, C37
- observability: C20 - every response carries `X-Request-ID`; worker logs are JSON with `document_id` and `run_id` (C53 greps them for the password)

## Handoff

- **Settled mid-build:** none
- **Dispatched:** none yet
- **Boundary:** S1-S5 backend proofs green in the working tree; nothing committed yet
- **Abandoned:** a `ProcessPoolExecutor` for inspection and parsing (it cannot kill a hung child; AD-026)
- **Walked:** not yet
