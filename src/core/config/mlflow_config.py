from typing import Any
import os
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class MLFlowConfig(BaseSettings):
    """MLFlow tracking and registry configuration."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )

    mlflow_tracking_uri: str = Field(default="databricks", description="MLFlow tracking URI")
    mlflow_registry_uri: str = Field(default="databricks-uc", description="MLFlow registry URI")
    mlflow_experiment_id: str = Field(..., description="MLFlow experiment ID")
    enable_tracing: bool = Field(default=True, description="Enable MLFlow tracing")

    def model_post_init(self, __context: Any) -> None:
        """Set MLFlow environment variables."""
        os.environ.setdefault("MLFLOW_TRACKING_URI", self.mlflow_tracking_uri)
        os.environ.setdefault("MLFLOW_REGISTRY_URI", self.mlflow_registry_uri)
        os.environ.setdefault("MLFLOW_EXPERIMENT_ID", self.mlflow_experiment_id)
