"""Check a model's JSON answer for one chunk: every page exactly once, nothing extra."""

import json
from typing import Any


def read_chunk_pages(raw: str, expected_pages: int) -> list[str] | None:
    """Return the chunk's page texts in order, or None when the answer is invalid.

    Invalid means not JSON, not the schema's shape, or page numbers that are not exactly
    ``1..expected_pages`` (a page missed, repeated or added).
    """
    try:
        data: Any = json.loads(_strip_fence(raw))
        items = data["pages"]
        by_number = {int(item["number"]): str(item["markdown"]) for item in items}
    except (ValueError, KeyError, TypeError):
        return None

    if len(items) != expected_pages or set(by_number) != set(range(1, expected_pages + 1)):
        return None
    return [by_number[number] for number in range(1, expected_pages + 1)]


def _strip_fence(raw: str) -> str:
    text = raw.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1] if "\n" in text else ""
        text = text.removesuffix("```").strip()
    return text
