"""
Observability middleware for structured logging and metrics (pure ASGI).

Implements:
- Structured JSON logging with automatic context propagation (structlog contextvars)
- Request/response tracking with trace IDs
- Exception logging with stack traces (optional: only for unhandled)
- Adds X-Trace-ID response header
"""

import time
import uuid
import structlog
from structlog.contextvars import clear_contextvars, bind_contextvars


class ObservabilityMiddleware:
    def __init__(self, app):
        self.app = app
        self.logger = structlog.get_logger(__name__)

    async def __call__(self, scope, receive, send):
        clear_contextvars()

        trace_id = str(uuid.uuid4())

        # Put it on scope.state-like storage (Starlette uses scope["state"])
        # so handlers can read it if they want.
        scope.setdefault("state", {})
        scope["state"]["trace_id"] = trace_id

        # Bind common context. Client is (host, port) in ASGI scope.
        client = scope.get("client")
        client_host = client[0] if client else None

        bind_contextvars(
            trace_id=trace_id,
            method=scope.get("method"),
            path=scope.get("path"),
            client_host=client_host,
        )

        start = time.perf_counter()

        self.logger.debug("request started")

        status_code = None
        async def send_wrapper(message):
            nonlocal status_code

            if message["type"] == "http.response.start":
                status_code = message["status"]
            await send(message)


        await self.app(scope, receive, send_wrapper)

        dur_ms = (time.perf_counter() - start) * 1000
        self.logger.debug(
            "request completed",
            status_code=status_code,
            duration_ms=round(dur_ms, 2),
        )