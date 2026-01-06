"""System API routes.

Health and readiness endpoints for monitoring and orchestration.
These endpoints do not require authentication.
"""

from datetime import datetime, timezone
from fastapi import APIRouter
from dependency_injector.wiring import inject, Provide

from core.core_container import CoreContainer
from app.api.system.dto.schemas import HealthCheckResponse

router = APIRouter()


@router.get("/health", response_model=HealthCheckResponse, tags=["System"])
@inject
async def health_check(
    fastapi_config=Provide[CoreContainer.fastapi_config],
):
    """Health check endpoint.

    Returns basic service health status without authentication.
    Used by load balancers and monitoring systems.
    """
    return HealthCheckResponse(
        status="healthy",
        version=fastapi_config.app_version,
        environment=fastapi_config.environment,
        timestamp=datetime.now(timezone.utc).isoformat(),
    )


@router.get("/ready", response_model=HealthCheckResponse, tags=["System"])
@inject
async def readiness_check(
    fastapi_config=Provide[CoreContainer.fastapi_config],
):
    """Readiness check endpoint.

    Indicates service is ready to accept traffic.
    Used by Kubernetes and orchestration platforms.
    """
    return HealthCheckResponse(
        status="healthy",
        version=fastapi_config.app_version,
        environment=fastapi_config.environment,
        timestamp=datetime.now(timezone.utc).isoformat(),
    )
