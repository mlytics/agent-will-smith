"""Centralized logging configuration using structlog.

This module configures structured logging with:
- Automatic context propagation via contextvars
- JSON output for production
- Proper log level filtering
- Callsite information (file, line, function)
"""

import logging
import structlog

from src.core.config.log_config import LogConfig


def configure_logging(log_config: LogConfig) -> None:
    """Configure structlog for the application.

    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        environment: Application environment (development, staging, production)
    """

    shared_processors = [
        structlog.contextvars.merge_contextvars,  # Auto-merge request context
        structlog.processors.add_log_level,
        structlog.processors.CallsiteParameterAdder(
            parameters=[
                structlog.processors.CallsiteParameter.FILENAME,
                structlog.processors.CallsiteParameter.LINENO,
                structlog.processors.CallsiteParameter.FUNC_NAME,
            ]
        ),
        structlog.processors.EventRenamer("message"),  # "event" → "message"
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]

    if log_config.log_format == "pretty":
        # Pretty printing for local development
        renderer = structlog.dev.ConsoleRenderer(colors=True)
    else:
        # JSON output for production
        renderer = structlog.processors.JSONRenderer()

    # Configure structlog
    structlog.configure(
        processors=shared_processors + [renderer],
        wrapper_class=structlog.make_filtering_bound_logger(log_config.log_level_int),
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    # Configure stdlib logging to use structlog
    logging.basicConfig(
        format="%(message)s",
        level=log_config.log_level_int,
    )