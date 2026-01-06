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
from src.core.exceptions import map_exception_to_http_status
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


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler."""
    # trace_id = getattr(request.state, "trace_id", None)
    # status_code, error_message = map_exception_to_http_status(exc)

    logger = structlog.get_logger(__name__)
    logger.error(
        "shit happens",
        exc_info=(type(exc), exc, exc.__traceback__) 
    )

    return JSONResponse(
        status_code=500,
    )
