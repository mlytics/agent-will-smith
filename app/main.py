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
from core.exceptions import map_exception_to_http_status
from app.middleware.observability import ObservabilityMiddleware
from app.gateway.dto.schemas import HealthCheckResponse
from app.gateway.product_recommendation.routes import router as product_recommendation_router

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
    
    Initializes dependencies at startup (從小組到大):
    1. Vector search client (connection pooling)
    2. More dependencies in future commits

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
    
    # Initialize dependencies (從小組到大 - from small to big)
    logger.info("initializing_dependencies")
    
    # Import infrastructure and workflow from agent
    from agent.product_recommendation.infra.vector_search import get_vector_search_client
    from agent.product_recommendation.infra.llm_client import get_llm_client
    from agent.product_recommendation.workflow import get_workflow
    from agent.product_recommendation.infra.prompts import load_prompt_from_registry
    from agent.product_recommendation.config import agent_config
    
    # 1. Vector search client (小 - small component)
    vector_client = get_vector_search_client()
    logger.info("vector_search_client_pooled")
    
    # 2. LLM client (小 - small component)
    llm_client = get_llm_client()
    logger.info("llm_client_pooled")
    
    # 3. Prompt cache (小 - small component)
    prompt = load_prompt_from_registry(agent_config.prompt_name)
    logger.info("prompt_cached", prompt_length=len(prompt.text))
    
    # 4. Workflow (大 - big component, composed of above with DI)
    workflow = get_workflow()
    logger.info("workflow_with_dependencies_ready")

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
            "detail": str(exc) if config.fastapi.environment == "development" else None,
            "trace_id": trace_id,
        },
    )

