"""Observability middleware for structured logging and metrics.

Implements:
- Structured JSON logging (guideline: "Log state, not vibes")
- Request/response tracking with trace IDs
- CPU/Memory metrics collection
- Exception handling with stack traces
"""

import time
import uuid
import psutil
import structlog
from typing import Callable
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.config import settings

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer(),
    ],
    wrapper_class=structlog.stdlib.BoundLogger,
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger(__name__)


class ObservabilityMiddleware(BaseHTTPMiddleware):
    """Middleware for request/response logging and metrics collection."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request with observability instrumentation.

        Args:
            request: Incoming HTTP request
            call_next: Next middleware/route handler

        Returns:
            HTTP response with trace ID header
        """
        # Generate trace ID for request tracking
        trace_id = str(uuid.uuid4())
        request.state.trace_id = trace_id

        # Capture start metrics
        start_time = time.time()
        process = psutil.Process()
        start_cpu = process.cpu_percent()
        start_memory = process.memory_info().rss / 1024 / 1024  # MB

        # Bind trace ID to logger context
        log = logger.bind(
            trace_id=trace_id,
            method=request.method,
            path=request.url.path,
            client_host=request.client.host if request.client else None,
        )

        log.info("request_started")

        try:
            # Process request
            response = await call_next(request)

            # Calculate metrics
            duration_ms = (time.time() - start_time) * 1000
            end_cpu = process.cpu_percent()
            end_memory = process.memory_info().rss / 1024 / 1024  # MB

            # Log successful request
            log.info(
                "request_completed",
                status_code=response.status_code,
                duration_ms=round(duration_ms, 2),
                cpu_delta_percent=round(end_cpu - start_cpu, 2),
                memory_mb=round(end_memory, 2),
                memory_delta_mb=round(end_memory - start_memory, 2),
            )

            # Add trace ID to response header
            response.headers["X-Trace-ID"] = trace_id

            return response

        except Exception as exc:
            # Calculate metrics even on error
            duration_ms = (time.time() - start_time) * 1000
            end_cpu = process.cpu_percent()
            end_memory = process.memory_info().rss / 1024 / 1024  # MB

            # Log error with full context
            log.error(
                "request_failed",
                error=str(exc),
                error_type=type(exc).__name__,
                duration_ms=round(duration_ms, 2),
                cpu_delta_percent=round(end_cpu - start_cpu, 2),
                memory_mb=round(end_memory, 2),
                memory_delta_mb=round(end_memory - start_memory, 2),
                exc_info=True,  # Include stack trace
            )

            # Return structured error response
            return JSONResponse(
                status_code=500,
                content={
                    "error": "Internal server error",
                    "detail": str(exc) if settings.environment == "development" else None,
                    "trace_id": trace_id,
                },
                headers={"X-Trace-ID": trace_id},
            )


def get_system_metrics() -> dict:
    """Get current system metrics.

    Returns:
        Dictionary with CPU and memory metrics
    """
    process = psutil.Process()
    return {
        "cpu_percent": round(process.cpu_percent(), 2),
        "memory_mb": round(process.memory_info().rss / 1024 / 1024, 2),
        "memory_percent": round(process.memory_percent(), 2),
    }

