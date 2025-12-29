"""FastAPI application configuration.

Configuration for API server, authentication, and observability.
"""

from typing import Literal
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class FastAPIConfig(BaseSettings):
    """FastAPI server and application configuration."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    app_name: str = Field(default="agent-will-smith", description="Application name")
    app_version: str = Field(default="0.1.0", description="Application version")
    environment: Literal["development", "staging", "production"] = Field(
        default="development", description="Environment name"
    )
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(
        default="INFO", description="Logging level"
    )

    # API Server
    port: int = Field(default=8000, description="API port")
    reload: bool = Field(default=False, description="Enable auto-reload (dev only)")

    # Authentication
    api_key: str = Field(
        default="dev-api-key-replace-in-production",
        description="Bearer token for API authentication",
    )

    # Observability
    enable_tracing: bool = Field(default=True, description="Enable MLFlow tracing")
    enable_metrics: bool = Field(default=True, description="Enable metrics collection")
    metrics_interval_seconds: int = Field(
        default=60, description="Metrics collection interval"
    )

