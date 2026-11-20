# Live smoke test against the real OpenRouter (outcome only)

The user filled `OPENROUTER_API_KEY` in the local `.env` before S5 was done, so one live smoke
test ran on the main Compose stack (`docker compose up`, page on `http://localhost:8080`). Only
the outcome is recorded here: no key, token or session value.

| When (UTC) | What | Outcome |
| --- | --- | --- |
| 2026-11-20 | `samples/w3c-dummy.pdf` (1 page) uploaded through nginx with `parser=pypdf` | `ready`; one text page; a markdown summary written by `google/gemini-3.1-flash-lite`, checked by `meta-llama/llama-guard-4-12b` before and after |
| 2026-11-20 | the first summary came back in Spanish for an English document | the summary prompt now names the document's language rule (`prompt_builder.py`, criterion 27) |
| 2026-11-20 | a summary call hung for minutes (OpenRouter keeps slow calls open with whitespace) | every attempt now has a hard 60 s deadline (AD-028); the hung job was reclaimed after `JOB_CLAIM_IDLE_MS` with `deliveries` 2, which also showed criterion 35 live |
| 2026-11-20 | Llama Guard 4 answered noise for the 85-page Constitution sent whole | the guard now reads 20,000-character pieces and treats an unreadable verdict as transient (AD-027) |

Spend on the shared key for these runs: well under $0.05 (the diagnostic guard calls cost about
$0.0135). Every automated test and proof after this uses fakes, respx or the local stub.
