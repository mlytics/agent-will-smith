"""FastAPI application entry point.

Main application setup with middleware, routes, and lifecycle management.
Follows guideline: "One controller of flow" - FastAPI handles HTTP orchestration.
"""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import mlflow
import signal
import structlog
import sys

from src.core.core_container import CoreContainer
from src.core.logger import configure_logging
from src.core.exceptions import (
    AgentException,
    BadRequestError,
    DomainValidationError,
    UnauthorizedError,
    ForbiddenError,
    NotFoundError,
    ConflictError,
    RateLimitedError,
    AgentStateError,
    ToolExecutionError,
    AgentTimeoutError,
    AgentCancelledError,
    UpstreamError,
    UpstreamTimeoutError,
    UpstreamRateLimitError,
    PromptLoadError,
    NoResultsFoundError,
)
from src.app.middleware.observability_middleware import ObservabilityMiddleware
from src.app.middleware.auth_middleware import AuthMiddleware
from src.app.api.system.routes import router as system_router
from src.app.api.product_recommendation.routes import router as product_recommendation_router


# Global container instance
_core_container = CoreContainer()


def setup_signal_handlers(app: FastAPI) -> None:
    """Setup signal handlers for graceful shutdown.

    Handles SIGTERM (Docker stop) and SIGINT (Ctrl+C) for zero-downtime deployments.
    """
    logger = structlog.get_logger(__name__)

    def signal_handler(sig, frame):
        """Handle shutdown signals gracefully."""
        sig_name = signal.Signals(sig).name
        logger.info("shutdown_signal_received", signal=sig_name)

        # FastAPI/Uvicorn will handle cleanup automatically
        # We just log and exit cleanly
        logger.info("application_shutdown_complete")
        sys.exit(0)

    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)
    logger.info("signal_handlers_registered", signals=["SIGTERM", "SIGINT"])


def create_app() -> FastAPI:
    """Create and configure FastAPI application.

    Centralizes all initialization logic:
    1. Configuration
    2. Logging
    3. MLflow
    4. DI Container & Wiring
    5. FastAPI App & Middleware
    6. Routes
    """
    # 1. Configuration
    fastapi_config = _core_container.fastapi_config()
    mlflow_config = _core_container.mlflow_config()
    log_config = _core_container.log_config()

    # 2. Logging
    configure_logging(log_config)
    logger = structlog.get_logger(__name__)

    logger.info(
        "application_starting",
        fastapi_config=fastapi_config,
        mlflow_config=mlflow_config,
        log_config=log_config,
    )

    # 3. MLflow
    if mlflow_config.enable_tracing:
        mlflow.langchain.autolog()
        logger.info("mlflow tracing enabled")

    # 4. DI Container & Wiring
    logger.info("initializing di container")

    # Wire auth middleware
    _core_container.wire(modules=["src.app.middleware.auth_middleware"])

    # Wire system routes (health/ready endpoints)
    _core_container.wire(modules=["src.app.api.system.routes"])

    from src.agent.product_recommendation.container import Container

    # Instantiate agent container with core dependency
    # Note: We keep this reference alive implicitly as it's wired
    container = Container(core=_core_container)
    container.wire(modules=["src.app.api.product_recommendation.routes"])

    # 5. FastAPI App
    app = FastAPI(
        title=fastapi_config.app_name,
        version=fastapi_config.app_version,
        description="AI Agent Platform using Databricks vector search and LangChain",
        docs_url="/docs" if fastapi_config.enable_docs else None,
        redoc_url="/redoc" if fastapi_config.enable_docs else None,
    )

    # Middleware
    app.add_middleware(ObservabilityMiddleware)
    app.add_middleware(AuthMiddleware, excluded_paths=["/health", "/ready", "/docs", "/redoc", "/openapi.json"])

    # Routers
    # System routes (no prefix - root level)
    app.include_router(system_router, dependencies=[])

    # Agent routes
    app.include_router(product_recommendation_router, prefix="/api/v1", dependencies=[])

    # Setup graceful shutdown handlers
    setup_signal_handlers(app)

    logger.info("application_ready")

    return app


# Create the app (this runs the init logic)
app = create_app()


def _map_agent_exception_to_status(exc: AgentException) -> int:
    """Map AgentException to HTTP status code."""
    # Client errors (4xx)
    if isinstance(exc, BadRequestError):
        return 400
    if isinstance(exc, UnauthorizedError):
        return 401
    if isinstance(exc, ForbiddenError):
        return 403
    if isinstance(exc, (NotFoundError, NoResultsFoundError)):
        return 404
    if isinstance(exc, AgentCancelledError):
        return 408
    if isinstance(exc, ConflictError):
        return 409
    if isinstance(exc, DomainValidationError):
        return 422
    if isinstance(exc, (RateLimitedError, UpstreamRateLimitError)):
        return 429

    # Agent state errors (context-dependent)
    if isinstance(exc, AgentStateError):
        return 409 if exc.conflict else 500

    # Agent runtime errors
    if isinstance(exc, AgentTimeoutError):
        return 504
    if isinstance(exc, ToolExecutionError):
        return 502 if exc.details.get("is_external", False) else 500

    # Upstream errors (5xx)
    if isinstance(exc, (UpstreamError, PromptLoadError)):
        return 502
    if isinstance(exc, UpstreamTimeoutError):
        return 504

    # Fallback
    return 500


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler - maps all exceptions to HTTP responses."""
    logger = structlog.get_logger(__name__)
    trace_id = getattr(request.state, "trace_id", "unknown")

    # Determine status code and error details
    if isinstance(exc, AgentException):
        status_code = _map_agent_exception_to_status(exc)
        error_message = exc.message
        error_details = exc.details
    elif isinstance(exc, ValueError):
        status_code = 400
        error_message = f"Invalid value: {str(exc)}"
        error_details = {}
    elif isinstance(exc, KeyError):
        status_code = 400
        error_message = f"Missing required field: {str(exc)}"
        error_details = {}
    elif isinstance(exc, TimeoutError):
        status_code = 504
        error_message = "Request timed out"
        error_details = {}
    else:
        # Unknown exceptions
        status_code = 500
        error_message = "Internal server error"
        error_details = {}

    # Log with full context
    logger.error(
        "exception_handled",
        trace_id=trace_id,
        status_code=status_code,
        error_type=type(exc).__name__,
        error_message=error_message,
        error_details=error_details,
        exc_info=exc,
    )

    # Return JSON response
    response_body = {
        "error": error_message,
        "trace_id": trace_id,
        "details": error_details if error_details else None,
    }

    return JSONResponse(
        status_code=status_code,
        content=response_body,
    )
