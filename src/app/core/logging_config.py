"""Structured logging configuration."""

import logging
import sys
from typing import Any

import structlog
from structlog.types import FilteringBoundLogger

from .settings import get_settings


def setup_logging() -> FilteringBoundLogger:
    """Configure structured logging with structlog."""
    settings = get_settings()

    # Determine log level
    log_level = getattr(logging, settings.log_level.upper(), logging.INFO)

    # Configure standard library logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=log_level,
    )

    # Shared processors for both dev and prod
    shared_processors = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
    ]

    if settings.log_format == "json":
        # Production JSON logging
        structlog.configure(
            processors=shared_processors
            + [
                structlog.processors.format_exc_info,
                structlog.processors.JSONRenderer(),
            ],
            wrapper_class=structlog.stdlib.BoundLogger,
            context_class=dict,
            logger_factory=structlog.stdlib.LoggerFactory(),
            cache_logger_on_first_use=True,
        )
    else:
        # Development console logging
        structlog.configure(
            processors=shared_processors
            + [
                structlog.dev.ConsoleRenderer(colors=True),
            ],
            wrapper_class=structlog.stdlib.BoundLogger,
            context_class=dict,
            logger_factory=structlog.stdlib.LoggerFactory(),
            cache_logger_on_first_use=True,
        )

    return structlog.get_logger()


def get_logger(name: str) -> FilteringBoundLogger:
    """Get a logger instance."""
    return structlog.get_logger(name)


def log_request(request_id: str, **extra: Any) -> None:
    """Log request with context."""
    logger = get_logger(__name__)
    logger.info("request", request_id=request_id, **extra)


def log_pr_event(pr_id: int, event: str, **extra: Any) -> None:
    """Log PR-related event with context."""
    logger = get_logger(__name__)
    logger.info("pr_event", pr_id=pr_id, event=event, **extra)


def log_agent_execution(agent_name: str, duration_ms: float, **extra: Any) -> None:
    """Log agent execution metrics."""
    logger = get_logger(__name__)
    logger.info("agent_execution", agent=agent_name, duration_ms=duration_ms, **extra)
