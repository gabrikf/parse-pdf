# Failure feedback: retries tell the model what was wrong; failed cards say why (AD-056)

Criteria 31 and 43. Run on 2026-11-20 against the working tree that became the commit holding
this file.

## What the requirement says

- A chunk answer that is not JSON, not the schema's shape, or misses, repeats or adds a page is
  retried up to 2 more times, each retry carrying one message that says what the last answer got
  wrong. After the third wrong answer the document is `dead` with `model_output_invalid` and a
  hint naming the document's page range and the problem.
- A guardrail rejection carries a hint naming each flagged category and whether the document's
  text or the summary was flagged.
- The person sees nothing while retries run; only the final card.

## Backend gates

- `ruff check backend`, `ruff format --check backend`: passed.
- `mypy` (strict): no issues in 154 source files. `lint-imports`: 3 contracts kept, 0 broken.
- `scripts/coverage-gate.sh` with `compose.test.yaml` up: 297 passed, total coverage 96.30%
  (gate 85%).
- New tests: `tests/unit/test_chunk_check.py` (each problem kind, the correction text, the hint
  in document page numbers), `tests/unit/test_model_page_parser.py` (the retry's third message,
  only the latest problem per retry, the hint for pages 4-5), `tests/unit/test_guardrail_hint.py`,
  `tests/unit/test_summary_service.py` (hint for input and for summary, verdict categories),
  `tests/integration/test_process_failures.py` (the hint read back through
  `GET /api/v1/documents/{id}`).

## Frontend gates

- `npm --prefix frontend run lint`, `typecheck`: passed. `test` (vitest): 23 passed.
- Playwright against the e2e stack (`scripts/proofs/e2e-stack.sh`, OpenRouter stub): 180 passed
  across 6 projects (375, 768, 1280 px, light and dark).

## Frontend proof

- Route: `/` on the e2e stack (`http://localhost:8081`).
- Did: uploaded `flagged.pdf`, whose text holds the stub's `STUB-UNSAFE` marker, with PyPDF;
  opened the Failed chip.
- Requirement: the failed card names the flagged category and where it was flagged.
- Screen showed: "The safety check flagged the document's text for violent crimes (S1), so no
  summary was written. A retry with the same text will most likely be flagged again." with
  Retry, Reparse with another parser and Delete forever. Pictures:
  `evidence/e2e/screens/*/dead-card-guardrail-hint.jpg`.
- Not shown on a screen: the `model_output_invalid` hint. The e2e stub always answers valid
  pages; that hint is proven by the unit tests above and travels the same `hint` field as the
  guardrail hint, which is shown.
