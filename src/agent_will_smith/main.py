"""FastAPI application entry point.

Main application setup with middleware, routes, and lifecycle management.
Follows guideline: "One controller of flow" - FastAPI handles HTTP orchestration.
"""

import os
from fastapi import FastAPI
import mlflow
import signal
import structlog
import sys

from agent_will_smith.core.container import Container as CoreContainer
from agent_will_smith.infra.container import Container as InfraContainer
from agent_will_smith.core.logger import configure_logging
from agent_will_smith.app.exception_handlers import register_exception_handlers
from agent_will_smith.app.middleware.observability_middleware import ObservabilityMiddleware
from agent_will_smith.app.middleware.auth_middleware import AuthMiddleware
from agent_will_smith.app.api.system.router import router as system_router
from agent_will_smith.app.api.product_recommendation.router import router as product_recommendation_router


# Global container instance
_core_container = CoreContainer()
_infra_container = InfraContainer(core_container=_core_container)


def setup_signal_handlers(app: FastAPI) -> None:
    """Setup signal handlers for graceful shutdown.

    Handles SIGTERM (Docker stop) and SIGINT (Ctrl+C) for zero-downtime deployments.
    """
    logger = structlog.get_logger(__name__)

    def signal_handler(sig, frame):
        """Handle shutdown signals gracefully."""
        sig_name = signal.Signals(sig).name
        logger.info("shutdown signal received", signal=sig_name)

        # FastAPI/Uvicorn will handle cleanup automatically
        # We just log and exit cleanly
        logger.info("application shutdown complete")
        sys.exit(0)

    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)
    logger.info("signal handlers registered", signals=["SIGTERM", "SIGINT"])


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
    databricks_config = _core_container.databricks_config()
    gemini_config = _core_container.gemini_config()

    # 2. Logging
    configure_logging(log_config)
    logger = structlog.get_logger(__name__)

    logger.info(
        "application starting",
        fastapi_config=fastapi_config,
        mlflow_config=mlflow_config,
        log_config=log_config,
        databricks_config=databricks_config,
        gemini_config=gemini_config,
    )

    # 3. MLflow
    if mlflow_config.enable_tracing:
        # Set tracking URI explicitly (more reliable than env vars alone)
        if mlflow_config.tracking_uri:
            mlflow.set_tracking_uri(mlflow_config.tracking_uri)
            logger.info("mlflow tracking uri set", uri=mlflow_config.tracking_uri)
        
        # Set experiment by numeric ID
        if mlflow_config.experiment_id:
            mlflow.set_experiment(experiment_id=mlflow_config.experiment_id)
            logger.info("mlflow experiment set", experiment_id=mlflow_config.experiment_id)
        
        # Enable autolog for LangChain (automatically traces LLM calls)
        mlflow.langchain.autolog()
        logger.info("mlflow tracing enabled")

    # 4. DI Container & Wiring
    logger.info("initializing di container")

    # Wire auth middleware
    _core_container.wire(modules=["agent_will_smith.app.middleware.auth_middleware"])

    # Wire system routes (health/ready endpoints)
    _core_container.wire(modules=["agent_will_smith.app.api.system.router"])

    from agent_will_smith.agent.product_recommendation.container import Container

    # Instantiate agent container with core and infra dependencies
    # Note: We keep this reference alive implicitly as it's wired
    # ProductRegistry validates config completeness on construction (fail fast)
    container = Container(core_container=_core_container, infra_container=_infra_container)
    
    # Eagerly initialize product registry to fail fast on config errors
    container.product_registry()
    logger.info("product registry initialized and validated")
    
    container.wire(modules=["agent_will_smith.app.api.product_recommendation.router"])

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

    # Exception handlers
    register_exception_handlers(app)

    # Routers
    # System routes (no prefix - root level)
    app.include_router(system_router, dependencies=[])

    # Agent routes
    app.include_router(product_recommendation_router, prefix="/api/v1", dependencies=[])

    # Setup graceful shutdown handlers
    setup_signal_handlers(app)

    logger.info("application ready")

    return app


# Create the app (this runs the init logic)
app = create_app()
