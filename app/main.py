"""FastAPI application entry point.

Main application setup with middleware, routes, and lifecycle management.
Follows guideline: "One controller of flow" - FastAPI handles HTTP orchestration.
"""

import os
from datetime import datetime, timezone
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import mlflow
import structlog

from app.config import settings
from app.middleware.auth import verify_api_key
from app.middleware.observability import ObservabilityMiddleware, get_system_metrics
from app.api.schemas import HealthCheckResponse
from app.api.routes import router as api_router

logger = structlog.get_logger(__name__)


def configure_databricks():
    """Configure Databricks environment variables."""
    os.environ["DATABRICKS_HOST"] = settings.databricks_host
    os.environ["DATABRICKS_CLIENT_ID"] = settings.databricks_client_id
    os.environ["DATABRICKS_CLIENT_SECRET"] = settings.databricks_client_secret


def configure_mlflow():
    """Configure MLFlow for tracking and tracing."""
    os.environ["MLFLOW_TRACKING_URI"] = settings.mlflow_tracking_uri
    os.environ["MLFLOW_REGISTRY_URI"] = settings.mlflow_registry_uri
    os.environ["MLFLOW_EXPERIMENT_ID"] = settings.mlflow_experiment_id

    # Enable MLFlow tracing if configured
    if settings.enable_tracing:
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
        app_name=settings.app_name,
        version=settings.app_version,
        environment=settings.environment,
    )

    configure_databricks()
    configure_mlflow()

    logger.info("application_ready", host=settings.host, port=settings.port)

    yield

    # Shutdown
    logger.info("application_shutting_down")


# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Product recommendation agent using Databricks vector search and LangChain",
    lifespan=lifespan,
    docs_url="/docs" if settings.environment == "development" else None,
    redoc_url="/redoc" if settings.environment == "development" else None,
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
        version=settings.app_version,
        environment=settings.environment,
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
        version=settings.app_version,
        environment=settings.environment,
        timestamp=datetime.now(timezone.utc).isoformat(),
    )


@app.get("/metrics", tags=["Observability"])
async def metrics(request: Request):
    """Expose system metrics for monitoring.

    Returns:
        System metrics (CPU, memory)
    """
    return {
        "trace_id": getattr(request.state, "trace_id", None),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "metrics": get_system_metrics(),
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
            "detail": str(exc) if settings.environment == "development" else None,
            "trace_id": trace_id,
        },
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.reload,
        log_level=settings.log_level.lower(),
    )

