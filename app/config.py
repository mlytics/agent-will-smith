"""Application configuration management.

All configuration is declarative and loaded from environment variables.
This follows the guideline: "Make configuration declarative."
"""

from typing import Literal
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

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
    host: str = Field(default="0.0.0.0", description="API host")
    port: int = Field(default=8000, description="API port")
    reload: bool = Field(default=False, description="Enable auto-reload (dev only)")

    # Authentication
    api_key: str = Field(
        default="dev-api-key-replace-in-production",
        description="Bearer token for API authentication",
    )

    # Databricks
    databricks_host: str = Field(..., description="Databricks workspace URL")
    databricks_client_id: str = Field(..., description="Databricks OAuth client ID")
    databricks_client_secret: str = Field(..., description="Databricks OAuth client secret")

    # MLFlow
    mlflow_tracking_uri: str = Field(default="databricks", description="MLFlow tracking URI")
    mlflow_registry_uri: str = Field(
        default="databricks-uc", description="MLFlow registry URI"
    )
    mlflow_experiment_id: str = Field(..., description="MLFlow experiment ID")

    # LLM Configuration
    llm_endpoint: str = Field(
        default="databricks-gpt-5-mini", description="Databricks LLM endpoint name"
    )
    llm_temperature: float = Field(default=0.7, description="LLM temperature", ge=0.0, le=2.0)
    llm_max_tokens: int | None = Field(default=None, description="Max tokens for LLM response")

    # Vector Search
    vector_search_endpoint: str = Field(..., description="Databricks vector search endpoint name")
    activities_index: str = Field(
        default="aigc_sit.default.activities_mock",
        description="Databricks vector search index for activities",
    )
    books_index: str = Field(
        default="aigc_sit.default.books_mock",
        description="Databricks vector search index for books",
    )
    embedding_model: str = Field(
        default="databricks-gte-large-en", description="Embedding model name"
    )

    # Agent Configuration
    max_k_products: int = Field(default=10, description="Maximum number of products to return")
    max_agent_steps: int = Field(default=10, description="Maximum agent reasoning steps")
    agent_timeout_seconds: int = Field(
        default=60, description="Agent execution timeout in seconds"
    )

    # Prompt Management
    prompt_name: str = Field(
        default="prompts:/aigc_sit.intent_engine.product_recommendation_prompt/1",
        description="MLFlow prompt registry path",
    )

    # Observability
    enable_tracing: bool = Field(default=True, description="Enable MLFlow tracing")
    enable_metrics: bool = Field(default=True, description="Enable metrics collection")
    metrics_interval_seconds: int = Field(
        default=60, description="Metrics collection interval"
    )


# Global settings instance
settings = Settings()

