"""Observability middleware for structured logging and metrics.

Implements:
- Structured JSON logging with automatic context propagation
- Request/response tracking with trace IDs
- Exception handling with stack traces

Note: Logging is configured centrally in core/logger.py
"""

import time
import uuid
import structlog
from typing import Callable
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from structlog.contextvars import clear_contextvars, bind_contextvars


class ObservabilityMiddleware(BaseHTTPMiddleware):
    """Middleware for request/response logging and metrics collection."""

    def __init__(self, app):
        super().__init__(app)
        self.logger = structlog.get_logger(__name__)

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request with observability instrumentation.

        Args:
            request: Incoming HTTP request
            call_next: Next middleware/route handler

        Returns:
            HTTP response with trace ID header
        """
        # Clear any previous context to prevent leakage between requests
        clear_contextvars()

        # Generate trace ID for request tracking
        trace_id = str(uuid.uuid4())
        request.state.trace_id = trace_id

        # Bind context for automatic propagation across all logs in this request
        bind_contextvars(
            trace_id=trace_id,
            method=request.method,
            path=request.url.path,
            client_host=request.client.host if request.client else None,
        )

        # Capture start time
        start_time = time.time()

        self.logger.debug("request started")

        # Process request
        response = await call_next(request)

        # Calculate duration
        duration_ms = (time.time() - start_time) * 1000

        # Log successful request (trace_id auto-included via contextvars)
        self.logger.debug(
            "request completed",
            status_code=response.status_code,
            duration_ms=round(duration_ms, 2),
        )

        # Add trace ID to response header
        response.headers["X-Trace-ID"] = trace_id

        return response
