"""Shared API schemas.

Common request/response schemas used across multiple agents.
Agent-specific schemas live in their respective gateway folders.
"""

from typing import Literal
from pydantic import BaseModel, Field


class HealthCheckResponse(BaseModel):
    """Health check response schema."""

    status: Literal["healthy", "unhealthy"] = Field(..., description="Service health status")
    version: str = Field(..., description="Application version")
    environment: str = Field(..., description="Environment name")
    timestamp: str = Field(..., description="Current timestamp (ISO 8601)")


class ErrorResponse(BaseModel):
    """Standard error response schema."""

    error: str = Field(..., description="Error message")
    detail: str | None = Field(None, description="Detailed error information (dev only)")
    trace_id: str | None = Field(None, description="Trace ID for debugging")
