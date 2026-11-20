"""Structured JSON logs carrying the request id; nothing user-supplied is logged raw."""

import logging
import sys

import structlog
from structlog.typing import EventDict, WrappedLogger

from app.core.request_context import current_request_id


def _add_request_id(_logger: WrappedLogger, _method: str, event: EventDict) -> EventDict:
    event.setdefault("request_id", current_request_id())
    return event


def configure_logging(level: str) -> None:
    """Route stdlib and structlog output to stdout as one JSON object per line."""
    logging.basicConfig(format="%(message)s", stream=sys.stdout, level=level.upper())
    for noisy in ("httpx", "httpcore", "pypdf", "botocore", "aiobotocore"):
        logging.getLogger(noisy).setLevel(logging.WARNING)
    logging.getLogger("pypdf").setLevel(logging.ERROR)
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            _add_request_id,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso", utc=True),
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(logging.getLevelName(level.upper())),
        logger_factory=structlog.PrintLoggerFactory(file=sys.stdout),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str) -> structlog.typing.FilteringBoundLogger:
    """Return a logger bound to a component name."""
    logger: structlog.typing.FilteringBoundLogger = structlog.get_logger(component=name)
    return logger
