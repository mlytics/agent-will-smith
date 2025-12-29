"""Common infrastructure configuration (Databricks + MLFlow).

Shared configuration for Databricks services and MLFlow tracking.
"""

import os
from typing import Any
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class DatabricksConfig(BaseSettings):
    """Databricks workspace configuration with OAuth authentication."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    databricks_host: str = Field(..., description="Databricks workspace URL")
    databricks_client_id: str = Field(..., description="Databricks OAuth client ID")
    databricks_client_secret: str = Field(..., description="Databricks OAuth client secret")

    def model_post_init(self, __context: Any) -> None:
        """Set Databricks environment variables for SDK compatibility."""
        os.environ.setdefault("DATABRICKS_HOST", self.databricks_host)
        os.environ.setdefault("DATABRICKS_CLIENT_ID", self.databricks_client_id)
        os.environ.setdefault("DATABRICKS_CLIENT_SECRET", self.databricks_client_secret)


class MLFlowConfig(BaseSettings):
    """MLFlow tracking and registry configuration."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    mlflow_tracking_uri: str = Field(default="databricks", description="MLFlow tracking URI")
    mlflow_registry_uri: str = Field(
        default="databricks-uc", description="MLFlow registry URI"
    )
    mlflow_experiment_id: str = Field(..., description="MLFlow experiment ID")

    def model_post_init(self, __context: Any) -> None:
        """Set MLFlow environment variables."""
        os.environ.setdefault("MLFLOW_TRACKING_URI", self.mlflow_tracking_uri)
        os.environ.setdefault("MLFLOW_REGISTRY_URI", self.mlflow_registry_uri)
        os.environ.setdefault("MLFLOW_EXPERIMENT_ID", self.mlflow_experiment_id)

