"""FastAPI application entry point.

Main application setup with middleware, routes, and lifecycle management.
Follows guideline: "One controller of flow" - FastAPI handles HTTP orchestration.
"""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import mlflow
import structlog

from core.core_container import CoreContainer
from core.logger import configure_logging
from core.exceptions import map_exception_to_http_status
from app.middleware.observability_middleware import ObservabilityMiddleware
from app.middleware.auth_middleware import AuthMiddleware
from app.api.system.routes import router as system_router
from app.api.product_recommendation.routes import router as product_recommendation_router


# Global container instance
_core_container = CoreContainer()


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

    # 2. Logging
    configure_logging(fastapi_config.log_level, fastapi_config.environment)
    logger = structlog.get_logger(__name__)

    logger.info(
        "application_starting",
        app_name=fastapi_config.app_name,
        version=fastapi_config.app_version,
        environment=fastapi_config.environment,
    )

    # 3. MLflow
    if mlflow_config.enable_tracing:
        mlflow.langchain.autolog()
        logger.info("mlflow_tracing_enabled")

    # 4. DI Container & Wiring
    logger.info("initializing_di_container")

    # Wire auth middleware
    _core_container.wire(modules=["app.middleware.auth_middleware"])

    # Wire system routes (health/ready endpoints)
    _core_container.wire(modules=["app.api.system.routes"])

    from agent.product_recommendation.container import Container

    # Instantiate agent container with core dependency
    # Note: We keep this reference alive implicitly as it's wired
    container = Container(core=_core_container)
    container.wire(modules=["app.api.product_recommendation.routes"])

    # 5. FastAPI App
    app = FastAPI(
        title=fastapi_config.app_name,
        version=fastapi_config.app_version,
        description="AI Agent Platform using Databricks vector search and LangChain",
        docs_url="/docs" if fastapi_config.environment == "development" else None,
        redoc_url="/redoc" if fastapi_config.environment == "development" else None,
    )

    # Middleware
    app.add_middleware(ObservabilityMiddleware, environment=fastapi_config.environment)
    app.add_middleware(AuthMiddleware, excluded_paths=["/health", "/ready"])

    # Routers
    # System routes (no prefix - root level)
    app.include_router(system_router, dependencies=[])

    # Agent routes
    app.include_router(product_recommendation_router, prefix="/api/v1", dependencies=[])

    logger.info("application_ready", port=fastapi_config.port, log_level=fastapi_config.log_level)

    return app


# Create the app (this runs the init logic)
app = create_app()


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler."""
    fastapi_config = _core_container.fastapi_config()
    trace_id = getattr(request.state, "trace_id", None)
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
            "detail": str(exc) if fastapi_config.environment == "development" else None,
            "trace_id": trace_id,
        },
    )
