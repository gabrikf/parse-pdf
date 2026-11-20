"""Check the README and the demo kit against criteria 74-77.

    python3 scripts/proofs/check_readme.py sections|how-i-worked|budget|postman-and-samples

Prints one line per check and "result: PASSED" or "result: FAILED"; exits 1 on a failure.
"""

import json
import re
import sys
from collections.abc import Callable
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
README = ROOT / "README.md"
POSTMAN = ROOT / "docs" / "postman" / "parse-pdf.postman_collection.json"
SOURCES = ROOT / "samples" / "SOURCES.md"

SECTIONS = [
    "Quick start",
    "Demo with curl",
    "Postman collection",
    "Sample PDFs",
    "Architecture",
    "API reference",
    "Decisions",
    "Departures from the brief",
    "Gaps found in the brief",
    "Limits and budget",
    "How I worked",
    "Testing and evidence",
    "What I would do next",
    "Time spent",
]
HOW_I_WORKED = [
    "harness",
    "brief",
    "tlc-spec-lean",
    "frontend-blueprint",
    "slice by slice",
    "fresh-subagent review",
    "/review-before-push",
]
ROUTES = [
    ("POST", "/api/v1/sessions"),
    ("POST", "/api/v1/documents"),
    ("GET", "/api/v1/documents"),
    ("GET", "/api/v1/documents/{{documentId}}"),
    ("GET", "/api/v1/documents/{{documentId}}/pages"),
    ("POST", "/api/v1/documents/{{documentId}}/reparse"),
    ("POST", "/api/v1/documents/{{documentId}}/requeue"),
    ("DELETE", "/api/v1/documents/{{documentId}}"),
    ("GET", "/api/v1/budget"),
    ("GET", "/api/v1/health/live"),
    ("GET", "/api/v1/health/ready"),
]
SAMPLES = {
    "text": "w3c-dummy.pdf",
    "over 10 pages": "constitution-of-the-united-states.pdf",
    "scanned": "constitution-scanned-p1-3.pdf",
    "encrypted": "w3c-dummy-locked.pdf",
}


def report(ok: bool, line: str) -> bool:
    """Print one check and pass its outcome through."""
    sys.stdout.write(f"{'ok  ' if ok else 'FAIL'} {line}\n")
    return ok


def headings() -> list[str]:
    """The README's second-level headings, in order."""
    return re.findall(r"^## (.+)$", README.read_text(), flags=re.MULTILINE)


def section(title: str) -> str:
    """The body of one second-level section."""
    text = README.read_text()
    match = re.search(rf"^## {re.escape(title)}\n(.*?)(?=^## |\Z)", text, re.MULTILINE | re.DOTALL)
    return match.group(1) if match else ""


def check_sections() -> bool:
    """Every section of criterion 74, in order, with both diagrams under Architecture."""
    found = headings()
    in_order = [title for title in found if title in SECTIONS] == SECTIONS
    results = [report(in_order, f"sections in order: {found}")]
    architecture = section("Architecture")
    results.append(report("flowchart LR" in architecture, "architecture holds the flowchart"))
    results.append(
        report("stateDiagram-v2" in architecture, "architecture holds the state diagram")
    )
    api = section("API reference")
    results.append(
        report(
            '"data"' in api and '"error"' in api and '"meta"' in api,
            "API reference shows the envelope",
        )
    )
    results.append(
        report(
            "docker compose up" in section("Quick start"), "quick start is one docker compose up"
        )
    )
    return all(results)


def check_how_i_worked() -> bool:
    """The seven steps of criterion 75, in order."""
    body = section("How I worked").lower()
    positions = [body.find(step.lower()) for step in HOW_I_WORKED]
    results = [
        report(position >= 0, f"mentions {step!r}")
        for step, position in zip(HOW_I_WORKED, positions, strict=True)
    ]
    results.append(report(positions == sorted(positions), f"in order: {positions}"))
    return all(results)


def check_budget() -> bool:
    """$5 of credit, 3,000 model pages a day, and what running out looks like (criterion 76)."""
    body = section("Limits and budget")
    return all(
        [
            report("$5" in body, "states the key holds $5"),
            report("3,000 model pages" in body, "states the daily budget of 3,000 model pages"),
            report("provider_out_of_credits" in body, "names provider_out_of_credits"),
            report("out of credit" in body, "says what a reviewer sees when credit runs out"),
        ]
    )


def collection_routes() -> set[tuple[str, str]]:
    """Method and path (query dropped) of every request in the Postman collection."""
    found: set[tuple[str, str]] = set()
    stack = list(json.loads(POSTMAN.read_text())["item"])
    while stack:
        item = stack.pop()
        stack.extend(item.get("item", []))
        if "request" in item:
            raw = item["request"]["url"]["raw"].replace("{{baseUrl}}", "").split("?")[0]
            found.add((item["request"]["method"], raw))
    return found


def check_postman_and_samples() -> bool:
    """All 11 routes in the collection; each sample with a source and license (criterion 77)."""
    routes = collection_routes()
    results = [report(route in routes, f"collection has {route[0]} {route[1]}") for route in ROUTES]
    results.append(
        report(len(routes) == len(ROUTES), f"collection has exactly {len(ROUTES)} routes")
    )
    sources = SOURCES.read_text()
    for kind, name in SAMPLES.items():
        results.append(report((ROOT / "samples" / name).is_file(), f"{kind} sample {name} exists"))
        results.append(report(name in sources, f"{name} has a line in samples/SOURCES.md"))
    results.append(
        report(
            sources.count("License") + sources.count("license") >= 1, "SOURCES.md names licenses"
        )
    )
    password = re.search(r"Demo password: `([^`]+)`", sources)
    results.append(
        report(
            password is not None and password.group(1) in README.read_text(),
            "README prints the demo password",
        )
    )
    return all(results)


CHECKS: dict[str, Callable[[], bool]] = {
    "sections": check_sections,
    "how-i-worked": check_how_i_worked,
    "budget": check_budget,
    "postman-and-samples": check_postman_and_samples,
}

if __name__ == "__main__":
    if len(sys.argv) != 2 or sys.argv[1] not in CHECKS:
        raise SystemExit(__doc__)
    passed = CHECKS[sys.argv[1]]()
    sys.stdout.write(f"result: {'PASSED' if passed else 'FAILED'}\n")
    sys.exit(0 if passed else 1)
