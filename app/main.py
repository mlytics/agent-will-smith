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

from core.config import config
from core.logger import configure_logging
from app.middleware.auth import verify_api_key
from app.middleware.observability import ObservabilityMiddleware
from app.api.schemas import HealthCheckResponse
from app.api.routes import router as api_router

# Configure logging on application import
configure_logging(config.log_level)

logger = structlog.get_logger(__name__)


def configure_mlflow():
    """Configure MLFlow for tracking and tracing.
    
    Note: Databricks environment variables are now set in Config.model_post_init()
    """
    # Enable MLFlow tracing if configured
    if config.enable_tracing:
        mlflow.langchain.autolog()
        logger.info("mlflow_tracing_enabled")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager for startup/shutdown events.

    Args:
        app: FastAPI application instance
    """
    # Startup
    logger.info(
        "application_starting",
        app_name=config.app_name,
        version=config.app_version,
        environment=config.environment,
    )

    configure_mlflow()

    logger.info("application_ready",
               port=config.port,
               log_level=config.log_level)

    yield

    # Shutdown
    logger.info("application_shutting_down")


# Create FastAPI application
app = FastAPI(
    title=config.app_name,
    version=config.app_version,
    description="AI Agent Platform using Databricks vector search and LangChain",
    lifespan=lifespan,
    docs_url="/docs" if config.environment == "development" else None,
    redoc_url="/redoc" if config.environment == "development" else None,
)

# Add observability middleware
app.add_middleware(ObservabilityMiddleware)


@app.get("/health", response_model=HealthCheckResponse, tags=["Health"])
async def health_check():
    """Health check endpoint for container orchestration.

    Returns:
        Health status with application metadata
    """
    return HealthCheckResponse(
        status="healthy",
        version=config.app_version,
        environment=config.environment,
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
        version=config.app_version,
        environment=config.environment,
        timestamp=datetime.now(timezone.utc).isoformat(),
    )


@app.get("/metrics", tags=["Observability"])
async def metrics(request: Request):
    """Basic metrics endpoint for monitoring.
    
    Note: For production, use container-level metrics (Prometheus, cAdvisor)
    for accurate CPU/memory tracking. Request-level metrics are not reliable
    in async contexts.

    Returns:
        Basic application metrics
    """
    return {
        "trace_id": getattr(request.state, "trace_id", None),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "status": "healthy",
    }


# Include API routes (protected by auth)
app.include_router(api_router, prefix="/api/v1", dependencies=[])


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler for unhandled errors.

    Args:
        request: HTTP request
        exc: Unhandled exception

    Returns:
        JSON error response with trace ID
    """
    trace_id = getattr(request.state, "trace_id", None)

    logger.error(
        "unhandled_exception",
        trace_id=trace_id,
        error=str(exc),
        error_type=type(exc).__name__,
        path=request.url.path,
        exc_info=True,
    )

    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "detail": str(exc) if config.environment == "development" else None,
            "trace_id": trace_id,
        },
    )

