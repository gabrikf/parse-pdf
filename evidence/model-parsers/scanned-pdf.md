# Criterion 46: scanned PDF through both model parsers

date: 2026-11-20T01:56:01Z
what: a 3-page image-only PDF (no text layer, `tests/pdf_factory.make_image_pdf`) uploaded with each model parser; the worker's production wiring (`worker_loop`: OpenRouter HTTP client, call gate, retry policy) calls the local OpenRouter stub over real HTTP; the test reads the document and its pages back through the API.
requirement: status `ready`, every page non-empty with `format: markdown`, for `gpt-5-mini` and `gemini-3.1-flash-lite`.
real key: not used (tests never call the real OpenRouter).

```
tests/integration/test_model_parsers_stub.py::test_scanned_pdf_reaches_ready_with_markdown_pages[gemini-3.1-flash-lite] PASSED [ 50%]
tests/integration/test_model_parsers_stub.py::test_scanned_pdf_reaches_ready_with_markdown_pages[gpt-5-mini] PASSED [100%]
============================== 2 passed in 6.62s ===============================
```
