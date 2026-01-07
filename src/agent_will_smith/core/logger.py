"""Centralized logging configuration using structlog.

This module configures structured logging with:
- Automatic context propagation via contextvars
- JSON output for production
- Proper log level filtering
- Callsite information (file, line, function)
"""

import logging
import structlog
import sys

from agent_will_smith.core.config.log_config import LogConfig


def configure_logging(log_config: LogConfig) -> None:
    """Configure structlog for the application.

    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        environment: Application environment (development, staging, production)
    """

    processors = [
        structlog.contextvars.merge_contextvars,  # Auto-merge request context
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.CallsiteParameterAdder(
            parameters=[
                structlog.processors.CallsiteParameter.THREAD,
                structlog.processors.CallsiteParameter.PROCESS,
                structlog.processors.CallsiteParameter.MODULE,
                structlog.processors.CallsiteParameter.FILENAME,
                structlog.processors.CallsiteParameter.LINENO,
                structlog.processors.CallsiteParameter.FUNC_NAME,
            ]
        ),
        structlog.processors.EventRenamer("message"),  # "event" → "message"
        structlog.processors.TimeStamper(fmt="iso", utc=True),
    ]

    if log_config.format == "pretty":
        # Pretty printing for local development
        processors += [
            structlog.dev.ConsoleRenderer(
                colors=True,
            )
            ]
    else:
        # JSON output for production
        processors += [
            structlog.processors.JSONRenderer(),
        ]

    # Configure structlog
    structlog.configure(
        processors=processors,
        wrapper_class=structlog.make_filtering_bound_logger(log_config.level_int),
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    # Configure stdlib logging to use structlog
    logging.basicConfig(
        format="%(message)s",
        level=log_config.level_int,
        stream=sys.stdout,
    )

    # root_logger = structlog.get_logger()
    # def handle_exception(exc_type, exc_value, exc_traceback):
    #     """
    #     Log any uncaught exception instead of letting it be printed by Python
    #     (but leave KeyboardInterrupt untouched to allow users to Ctrl+C to stop)
    #     See https://stackoverflow.com/a/16993115/3641865
    #     """
    #     if issubclass(exc_type, KeyboardInterrupt):
    #         sys.__excepthook__(exc_type, exc_value, exc_traceback)
    #         return

    #     root_logger.error(
    #         "Uncaught exception", exc_info=(exc_type, exc_value, exc_traceback)
    #     )

    # sys.excepthook = handle_exception