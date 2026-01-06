"""System API schemas.

Common system-level request/response schemas.
"""

from typing import Literal
from pydantic import BaseModel, Field


class HealthCheckResponse(BaseModel):
    """Health check response schema."""

    status: Literal["healthy", "unhealthy"] = Field(..., description="Service health status")
    version: str = Field(..., description="Application version")
    timestamp: str = Field(..., description="Current timestamp (ISO 8601)")
