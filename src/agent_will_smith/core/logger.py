"""Centralized logging configuration using structlog.

This module configures structured logging with:
- Automatic context propagation via contextvars
- JSON output for production
- Proper log level filtering
- Callsite information (file, line, function)
- Unified handler with ProcessorFormatter for consistent output
- Configurable 3rd party library log suppression
"""

import logging
import structlog
import sys

from agent_will_smith.core.config.log_config import LogConfig


class ThirdPartyLogFilter(logging.Filter):
    """Filter that suppresses 3rd party library logs below configured level.
    
    Allows agent_will_smith.* loggers to pass through at any level,
    while enforcing a minimum level (e.g., WARNING) for all other loggers.
    This is more reliable than per-library setLevel() calls since many
    libraries (mlflow, databricks, etc.) add their own handlers or override settings.
    """

    def __init__(self, third_party_level: int):
        """Initialize the filter.
        
        Args:
            third_party_level: Minimum log level for 3rd party libraries (e.g., logging.WARNING)
        """
        super().__init__()
        self.third_party_level = third_party_level

    def filter(self, record: logging.LogRecord) -> bool:
        """Filter log records based on logger name and level.
        
        Args:
            record: The log record to filter
            
        Returns:
            True if the record should be logged, False otherwise
        """
        # Allow our app logs at any level (root logger controls this)
        if record.name.startswith("agent_will_smith"):
            return True
        # 3rd party: only at configured level and above
        return record.levelno >= self.third_party_level


def configure_logging(log_config: LogConfig) -> None:
    """Configure structlog for the application with unified handler.

    This sets up:
    1. Structlog processors for structured logging
    2. ProcessorFormatter to route stdlib logging through structlog
    3. ThirdPartyLogFilter to suppress noisy 3rd party libraries
    
    Args:
        log_config: Logging configuration with level, format, and third_party_level
    """

    # Renderer selection based on format
    if log_config.format == "pretty":
        renderer = structlog.dev.ConsoleRenderer(colors=True)
    else:
        renderer = structlog.processors.JSONRenderer()

    # Shared processors (used by both structlog and stdlib logging)
    shared_processors = [
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

    # Configure structlog - use ProcessorFormatter.wrap_for_formatter as final step
    # This passes the log event to the handler's ProcessorFormatter for rendering
    structlog.configure(
        processors=shared_processors + [
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        wrapper_class=structlog.make_filtering_bound_logger(log_config.level_int),
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    # Foreign pre-chain: preprocessing for stdlib logging before structlog processing
    # This ensures stdlib loggers get similar enrichment (logger name, level, timestamp, message key)
    foreign_pre_chain = [
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso", utc=True),
        structlog.processors.EventRenamer("message"),  # Rename 'event' to 'message' for consistency
    ]

    # Configure stdlib logging with unified handler + ProcessorFormatter
    # ProcessorFormatter applies the renderer to all logs (structlog + stdlib)
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(
        structlog.stdlib.ProcessorFormatter(
            processors=[
                structlog.stdlib.ProcessorFormatter.remove_processors_meta,
                renderer,
            ],
            foreign_pre_chain=foreign_pre_chain,
        )
    )

    # Add filter to suppress 3rd party library noise
    handler.addFilter(ThirdPartyLogFilter(log_config.third_party_level_int))

    # Configure root logger - clear any existing handlers first
    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.addHandler(handler)
    root_logger.setLevel(log_config.level_int)
