"""FastAPI application entry point.

Main application setup with middleware, routes, and lifecycle management.
Follows guideline: "One controller of flow" - FastAPI handles HTTP orchestration.
"""

from datetime import datetime, timezone
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import mlflow
import structlog

from core.container import CoreContainer
from core.logger import configure_logging
from core.exceptions import map_exception_to_http_status
from app.middleware.observability import ObservabilityMiddleware
from app.gateway.dto.schemas import HealthCheckResponse
from app.gateway.product_recommendation.routes import router as product_recommendation_router

# Remove global logger to avoid pre-config caching
# logger = structlog.get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager for startup/shutdown events.

    Centralized initialization of all infrastructure:
    1. Logging
    2. MLflow
    3. Dependency Injection
    """
    # 1. Initialize Logging
    # config.log_level is now resolved via container or default to info if eager logging needed
    # Ideally logging is also injected or configured via container
    core_container = CoreContainer()
    fastapi_config = core_container.fastapi_config()
    mlflow_config = core_container.mlflow_config()

    configure_logging(fastapi_config.log_level)
    logger = structlog.get_logger(__name__)

    logger.info(
        "application_starting",
        app_name=fastapi_config.app_name,
        version=fastapi_config.app_version,
        environment=fastapi_config.environment,
    )

    # 2. Initialize MLflow
    if mlflow_config.enable_tracing:
        mlflow.langchain.autolog()
        logger.info("mlflow_tracing_enabled")

    # 3. Initialize DI container (follows joke_agent pattern)
    logger.info("initializing_di_container")

    from agent.product_recommendation.container import Container

    # Wire auth middleware for dependency injection
    core_container.wire(modules=["app.middleware.auth"])

    # We pass the core container to the agent container if needed,
    # but declarative container usage (providers.Container) usually handles instantiation
    # or we can wire it here.

    # Since agent Container defines `core = providers.Container(CoreContainer)`,
    # we can override it with our instantiated core_container to share state/singletons.
    container = Container(core=core_container)
    container.wire(modules=["app.gateway.product_recommendation.routes"])
    logger.info("application_ready", port=fastapi_config.port, log_level=fastapi_config.log_level)

    yield

    # Shutdown
    logger.info("application_shutting_down")


# Create temporary container usage for app metadata (eager load)
# Note: In a pure DI world, we might delay this or load config separately.
# For now, we instantiate CoreContainer to get metadata.
_core = CoreContainer()
_fastapi_config = _core.fastapi_config()

# Create FastAPI application
app = FastAPI(
    title=_fastapi_config.app_name,
    version=_fastapi_config.app_version,
    description="AI Agent Platform using Databricks vector search and LangChain",
    lifespan=lifespan,
    docs_url="/docs" if _fastapi_config.environment == "development" else None,
    redoc_url="/redoc" if _fastapi_config.environment == "development" else None,
)

# Add observability middleware
app.add_middleware(ObservabilityMiddleware, environment=_fastapi_config.environment)


@app.get("/health", response_model=HealthCheckResponse, tags=["Health"])
async def health_check():
    """Health check endpoint for container orchestration.

    Returns:
        Health status with application metadata
    """
    return HealthCheckResponse(
        status="healthy",
        version=_fastapi_config.app_version,
        environment=_fastapi_config.environment,
        timestamp=datetime.now(timezone.utc).isoformat(),
    )


@app.get("/ready", response_model=HealthCheckResponse, tags=["Health"])
async def readiness_check():
    """Readiness check endpoint for container orchestration.

    Returns:
        Readiness status (can be enhanced with dependency checks)
    """
    # TODO: Add checks for Databricks connectivity, vector search availability, etc.
    return HealthCheckResponse(
        status="healthy",
        version=_fastapi_config.app_version,
        environment=_fastapi_config.environment,
        timestamp=datetime.now(timezone.utc).isoformat(),
    )


# Include API routes (protected by auth)
app.include_router(product_recommendation_router, prefix="/api/v1", dependencies=[])


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler for unhandled errors.

    Maps all exceptions to appropriate HTTP status codes using the
    exception hierarchy defined in core.exceptions.

    Args:
        request: HTTP request
        exc: Unhandled exception

    Returns:
        JSON error response with trace ID and appropriate status code
    """
    trace_id = getattr(request.state, "trace_id", None)

    # Map exception to HTTP status
    status_code, error_message = map_exception_to_http_status(exc)

    logger = structlog.get_logger(__name__)
    logger.error(
        "unhandled_exception",
        trace_id=trace_id,
        error=str(exc),
        error_type=type(exc).__name__,
        status_code=status_code,
        path=request.url.path,
        exc_info=True,
    )

    return JSONResponse(
        status_code=status_code,
        content={
            "error": error_message,
            "detail": str(exc) if _fastapi_config.environment == "development" else None,
            "trace_id": trace_id,
        },
    )
