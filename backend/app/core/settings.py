"""Typed runtime configuration read from the environment (and `.env` in development)."""

from functools import lru_cache

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

MIN_SECRET_BYTES = 32
DEFAULT_HEARTBEAT_PATH = "/tmp/worker-heartbeat"  # noqa: S108 - container-local file
SUMMARY_MODEL_PROVIDER = "google"
QUOTE_CHARS = "\"'`\u201c\u201d\u2018\u2019"


def normalize_model_id(raw: str, provider: str = SUMMARY_MODEL_PROVIDER) -> str:
    """Turn the brief's ``" gemini-3.1-flash-lite ”`` into an OpenRouter id.

    The brief writes the model id with a stray space and mismatched quotes, so the value is
    stripped of whitespace and every kind of quote, then prefixed with its provider when the
    prefix is missing.
    """
    cleaned = raw.strip().strip(QUOTE_CHARS).strip()
    if "/" in cleaned:
        return cleaned
    return f"{provider}/{cleaned}"


class Settings(BaseSettings):
    """Every knob of the API and the workers, validated once at start.

    A missing or short ``SESSION_SECRET`` stops the process with a message naming it, so a
    deployment can never sign sessions with a guessable key.
    """

    model_config = SettingsConfigDict(env_file=None, extra="ignore", frozen=True)

    session_secret: str = Field(min_length=1)
    page_origin: str = "http://localhost:8080"
    cookie_secure: bool = False

    redis_url: str = "redis://redis:6379/0"

    s3_endpoint_url: str = "http://storage:8333"
    s3_access_key: str = Field(min_length=1)
    s3_secret_key: str = Field(min_length=1)
    s3_region: str = "us-east-1"
    s3_bucket: str = "documents"

    openrouter_api_key: str = ""
    openrouter_base_url: str = "https://openrouter.ai/api/v1"
    openrouter_timeout_s: float = 60.0
    summary_model_id: str = "google/gemini-3.1-flash-lite"
    gemini_parser_model_id: str = "google/gemini-3.1-flash-lite"
    gpt_parser_model_id: str = "openai/gpt-5-mini"
    # One parse call must finish inside its deadline (AD-055): GPT-5 Mini writes ~60-90 tokens a
    # second, so it gets 3-page chunks and no reasoning; Gemini does 10 dense pages in ~15 s.
    gemini_parser_chunk_pages: int = Field(default=10, ge=1, le=10)
    gpt_parser_chunk_pages: int = Field(default=3, ge=1, le=10)
    gemini_parser_reasoning_effort: str = "low"
    gpt_parser_reasoning_effort: str = "minimal"
    openrouter_parse_timeout_s: float = 120.0
    guardrail_model_id: str = "meta-llama/llama-guard-4-12b"
    # Llama Guard categories that do not block a document (AD-054): S6 specialized advice,
    # S7 privacy, S8 intellectual property. Comma-separated; `none` blocks every category.
    guardrail_allowed_categories: str = "S6,S7,S8"

    model_page_budget_per_day: int = 3000
    openrouter_calls_per_minute: int = 30

    upload_requests_per_minute: int = 10
    uploads_in_flight_per_session: int = 2
    sessions_per_minute_per_ip: int = 20

    inspect_timeout_s: float = 10.0
    inspect_concurrency: int = 4
    pypdf_parse_timeout_s: float = 300.0

    job_claim_idle_ms: int = 60_000
    claim_refresh_s: float = 20.0
    reclaim_sweep_s: float = 15.0
    max_deliveries: int = 5
    shutdown_grace_s: float = 30.0
    heartbeat_path: str = DEFAULT_HEARTBEAT_PATH
    heartbeat_interval_s: float = 5.0

    log_level: str = "INFO"

    @field_validator("session_secret")
    @classmethod
    def _secret_is_long_enough(cls, value: str) -> str:
        if len(value.encode()) < MIN_SECRET_BYTES:
            raise ValueError(f"SESSION_SECRET must be at least {MIN_SECRET_BYTES} bytes")
        return value

    @property
    def guardrail_allowed(self) -> frozenset[str]:
        """The allowed Llama Guard categories as codes, upper case (``none`` gives none)."""
        codes = (code.strip().upper() for code in self.guardrail_allowed_categories.split(","))
        return frozenset(code for code in codes if code and code != "NONE")

    @field_validator("summary_model_id", "gemini_parser_model_id")
    @classmethod
    def _normalize_google_id(cls, value: str) -> str:
        return normalize_model_id(value)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Read the settings once per process."""
    return Settings()
