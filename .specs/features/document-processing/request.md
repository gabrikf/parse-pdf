# Request - document-processing

Saved verbatim on 2026-11-19, before anything else (tlc-spec-lean rule 7). Invoked as
`/tlc-spec-lean`. The `task:` block is summarized here; its verbatim text is in the local,
gitignored `docs/private/test-task.md` (and the original `docs/private/BWAI2.1_test_task.docx`).
Reviewers read the verbatim file. Everything after `my decisions:` is verbatim.

Captures: none.

---

task: (the brief, verbatim, is in `docs/private/test-task.md`, kept out of git with the original
`docs/private/BWAI2.1_test_task.docx` because the hiring company's test stays private)

In short: an async document processing app. Users upload one or more PDFs on a web page, pick a
parser (PyPDF, Gemini 3.1 Flash Lite or GPT-5 Mini), and later see per-page content as text or
markdown and one summary per file, written by Gemini 3.1 Flash Lite. Stack: Python 3.12+ with
FastAPI, Redis 7+ with Streams as the queue, Docker Compose, and React or Next.js. Priorities, top
first: a backend that serves concurrent requests, PyPDF upload and parsing, the Redis Streams queue,
the Gemini summary, GPT-5 Mini OCR, the frontend. A curl or Postman demo is acceptable, and the
delivery is a source zip without `.venv` or `node_modules`.

my decisions:

* Proof of concurrency. “Able to serve concurrent API requests” is the top priority. Use async FastAPI with `redis.asyncio`, and save a concurrent load test (for example `hey` or parallel curl) in `evidence/`.
* Crash recovery that’s shown. Workers reclaim stuck jobs with `XAUTOCLAIM`, a dead-letter after N tries, and a test that kills a worker mid-job.
* Retry on model rate limits. Retry Gemini 429s with backoff, so a rate limit retries instead of ending as `dead`.
* Compose. Healthchecks, `depends_on: condition: service_healthy`, and Redis AOF on so the queue survives a restart.
* Demo kit. A README with one `docker compose up`, a curl/Postman collection, and sample public PDFs. The task says a curl demo is acceptable.
* Tests. Integration tests against a real Redis in Compose, with mocked model providers.

Architecture

* D1 / AD-001: PDF bytes go to S3-compatible storage (MinIO locally). The document record lives in Redis. Queue messages carry only the id and the object key.
* D2 / AD-002: a job is acknowledged (XACK) only after a final status (`ready`, `no_text`, `dead`) is saved. A redelivered job never calls the parser or the model again.
* D3 / AD-005: one unacknowledged queue entry per document. Reparse and requeue are refused while it’s `queued` or `processing`.
* D7: parsing never runs inside the request. Workers scale with `docker compose up --scale worker=3`.

Parsing and models

* D6: three parsers: `pypdf`, `gemini-3.1-flash-lite`, `gpt-5-mini`. Each returns one string per page.
* D8 / AD-003: all model calls go through OpenRouter with one `OPENROUTER_API_KEY`. The uploader picks the model, and that model writes the summary.
* D5: empty or encrypted files are refused and not stored. Files over 50MB or 1000 pages are `too_large`. A PDF with no text becomes `no_text` and suggests Gemini.
* D4: each file in an upload is judged on its own. One bad file doesn’t fail the others.
* AD-004: `pages` and `summary` are visible only when the status is `ready`.

Security

* AD-006: CORS allows only the one page origin (`PAGE_ORIGIN`), never `*`.
* AD-007: Helmet-style headers on every response (`secure` `Preset.BASIC`).
* AD-008: uploads limited to 10 per minute and 2 in progress per client. OpenRouter calls limited to 30 per minute shared by all workers, and 1 at a time per worker.
* AD-009: a guardrail model checks text before the summary call and checks the output before it’s stored. A rejection saves `dead`.

Upload page

* One page with no router; it polls every 2 seconds instead of using websockets.
* Up to 20 files per upload, added by picker, drag-and-drop or paste.
* Asks for confirmation before reparse or requeue.
* TanStack Query and React Hook Form.
* English copy in sentence case; works at 375px and 1280px.
* The page talks only to your API, never directly to OpenRouter or Redis.
* Look: a full-bleed feed rather than a dashboard. One teal action (`#0F766E`), Newsreader and Schibsted Grotesk fonts, no shadows or gradients.

Testing lessons (not yet confirmed)

* Make tests check the literal values the spec names, every input including an omitted field and an empty string, and every final status.

use all the skills that would be worth it to guide the decisions.
one think that must be added on the specs is how I worked on this. so started by creating the harness, after read the task, and started spec lean to think about how can we implement it and after used the frontend-blueprint to create a dfesign to be able to think way more, comment ou it and in the end implement.

Cloud. Backend is the most important part here. So I want to put my juice on this request. For me, solid principles and clean architecture is very important, but I would like that you put some comments to explain the main classes and methods. But I want that you separate my files in folders that separate the logic and interfaces from the implementations, but maybe make it close one each other. But I want that you use like controllers, services, or use cases. Search what would be best seen, and providers, and all the very perfect good methods that you can turn this application into a solid one, and very, very, very easy to understand. Do not never put all the code glued. I want methods with space separation. Dev must read it and understand very easily. One file per responsibility is a must. I don't want big files. I want that we insert other use cases or providers or repositories inside of our services, to not make them big and difficult to understand. I want that it shine the eyes from the reviewers when they see it, and I want it very, very organized. It must be very, very bulletproof from receiving many requests. We need to be able to deal with it, and we must use all the things that task says. We will use open router. I will create one key to share with them. I need a README very well explained how I did this test, as I told you before. And all must pass through code review and so on. It must be very, very secure, fast, and top. On the front end, we want to be able to open it on cell phones, tablets, and everything. So now I just want to make the plan. After we create the plan, I will use other skill to build the designs. Just say if it would be better to start on a new session or in this current one. please serach on the web for similar tests that were very well seeing that stared and poeple loved to apply here. read carefully the task and find any think that they want to see in a good dev to prove and gaps that we can not see maybe or jokes.. lets to it in a top way
