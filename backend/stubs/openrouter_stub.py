"""A local OpenRouter stand-in for the e2e stack and the worker-kill test. Never production.

``POST /api/v1/chat/completions`` answers like OpenRouter:
- the guardrail model: ``safe`` (``unsafe\\nS1`` when the text holds ``STUB-UNSAFE``);
- a JSON-schema page request: one markdown page per page the prompt announces;
- anything else: a markdown summary.
Text holding a marker ``STUB-FAIL-ONCE-<token>`` gets one ``400`` for that token, then every
later call with it succeeds, so a document can be made ``dead`` and then retried.
``STUB_DELAY_S`` slows every answer.
"""

import asyncio
import json
import os
import re
from typing import Any

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

app = FastAPI(title="openrouter-stub")
FAILED_ONCE: set[str] = set()
PAGES_ANNOUNCED = re.compile(r"The attached PDF has (\d+) pages")
FAIL_ONCE_MARKER = re.compile(r"STUB-FAIL-ONCE-[A-Za-z0-9-]+")
CALLS: list[str] = []


def _text_of(messages: list[dict[str, Any]]) -> str:
    parts: list[str] = []
    for message in messages:
        content = message.get("content")
        if isinstance(content, str):
            parts.append(content)
        elif isinstance(content, list):
            parts += [item.get("text", "") for item in content if isinstance(item, dict)]
    return "\n".join(parts)


def _completion(content: str) -> dict[str, Any]:
    return {
        "id": "stub",
        "object": "chat.completion",
        "choices": [{"index": 0, "message": {"role": "assistant", "content": content}}],
    }


def _summary() -> str:
    return (
        "This document was summarized by the local OpenRouter stub. It stands in for "
        "gemini-3.1-flash-lite in the e2e stack. The real model writes three to six sentences "
        "here.\n\n### Key points\n- Parsed by the worker\n- Summarized once per file\n"
        "- Rendered as markdown"
    )


def _pages(count: int) -> str:
    pages = [
        {"number": n, "markdown": f"## Page {n}\n\nStub markdown for page {n}."}
        for n in range(1, count + 1)
    ]
    return json.dumps({"pages": pages})


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/calls")
async def calls() -> dict[str, list[str]]:
    return {"models": CALLS}


@app.post("/api/v1/chat/completions")
async def chat_completions(request: Request) -> JSONResponse:
    body = await request.json()
    model = str(body.get("model", ""))
    text = _text_of(body.get("messages", []))
    CALLS.append(model)
    await asyncio.sleep(float(os.environ.get("STUB_DELAY_S", "0")))

    marker = FAIL_ONCE_MARKER.search(text)
    if marker and marker.group(0) not in FAILED_ONCE:
        FAILED_ONCE.add(marker.group(0))
        return JSONResponse({"error": {"code": 400, "message": "stub refusal"}}, status_code=400)

    if "llama-guard" in model:
        return JSONResponse(_completion("unsafe\nS1" if "STUB-UNSAFE" in text else "safe"))
    if body.get("response_format"):
        match = PAGES_ANNOUNCED.search(text)
        return JSONResponse(_completion(_pages(int(match.group(1)) if match else 1)))
    return JSONResponse(_completion(_summary()))
