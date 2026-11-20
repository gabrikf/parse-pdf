"""Criterion 2 (SESSION_SECRET) and criterion 28 (the brief's model id)."""

import pytest
from pydantic import ValidationError

from app.core.settings import Settings, normalize_model_id
from app.serve import describe, main

REQUIRED = {"s3_access_key": "a", "s3_secret_key": "b"}


def test_unset_secret_is_refused(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("SESSION_SECRET", raising=False)
    with pytest.raises(ValidationError) as caught:
        Settings(**REQUIRED)  # type: ignore[arg-type]
    assert "SESSION_SECRET" in describe(caught.value)


def test_31_byte_secret_is_refused() -> None:
    with pytest.raises(ValidationError) as caught:
        Settings(session_secret="x" * 31, **REQUIRED)  # type: ignore[arg-type]
    assert "SESSION_SECRET" in describe(caught.value)
    assert "32 bytes" in describe(caught.value)


def test_32_byte_secret_starts() -> None:
    assert Settings(session_secret="x" * 32, **REQUIRED).session_secret == "x" * 32  # type: ignore[arg-type]


def test_serve_exits_1_naming_the_variable(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setenv("SESSION_SECRET", "short")
    monkeypatch.setenv("S3_ACCESS_KEY", "a")
    monkeypatch.setenv("S3_SECRET_KEY", "b")

    assert main() == 1
    assert "SESSION_SECRET" in capsys.readouterr().err


@pytest.mark.parametrize(
    "raw",
    [
        " gemini-3.1-flash-lite ”",
        "gemini-3.1-flash-lite",
        "google/gemini-3.1-flash-lite",
        "“ gemini-3.1-flash-lite ”",
        "'gemini-3.1-flash-lite'",
    ],
)
def test_brief_model_id_resolves_to_openrouter_id(raw: str) -> None:
    assert normalize_model_id(raw) == "google/gemini-3.1-flash-lite"


def test_settings_normalize_summary_model_id() -> None:
    settings = Settings(
        session_secret="x" * 32,
        summary_model_id=" gemini-3.1-flash-lite ”",
        **REQUIRED,  # type: ignore[arg-type]
    )
    assert settings.summary_model_id == "google/gemini-3.1-flash-lite"


def test_guardrail_allows_document_categories_by_default() -> None:
    settings = Settings(session_secret="x" * 32, **REQUIRED)  # type: ignore[arg-type]

    assert settings.guardrail_allowed == frozenset({"S6", "S7", "S8"})


@pytest.mark.parametrize(
    ("raw", "allowed"),
    [("none", set()), ("NONE", set()), ("", set()), (" s6 , S12,", {"S6", "S12"}), ("S7", {"S7"})],
)
def test_guardrail_allowed_categories_are_parsed(raw: str, allowed: set[str]) -> None:
    settings = Settings(
        session_secret="x" * 32,
        guardrail_allowed_categories=raw,
        **REQUIRED,  # type: ignore[arg-type]
    )

    assert settings.guardrail_allowed == frozenset(allowed)
