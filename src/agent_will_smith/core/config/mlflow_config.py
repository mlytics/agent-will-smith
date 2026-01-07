from typing import Any, Optional
import os
from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class MLFlowConfig(BaseSettings):
    """MLFlow tracking and registry configuration."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="CORE_MLFLOW_",
        case_sensitive=False,
    )

    tracking_uri: Optional[str] = Field(None, description="MLFlow tracking URI")
    registry_uri: Optional[str] = Field(None, description="MLFlow registry URI")
    experiment_id: Optional[str] = Field(None, description="MLFlow experiment ID")
    enable_tracing: bool = Field(default=False, description="Enable MLFlow tracing")

    @model_validator(mode="after")
    def check_tracking_config(self) -> "MLFlowConfig":
        """Validate that either tracking URI, experiment ID, or registry URI is provided if tracing is enabled."""
        if self.enable_tracing and not (self.tracking_uri or self.experiment_id or self.registry_uri):
            raise ValueError("Enable tracing requires either tracking URI, experiment ID, or registry URI.")
        return self

    def model_post_init(self, __context: Any) -> None:
        """Set MLFlow environment variables."""
        if self.enable_tracing:
            os.environ.setdefault("MLFLOW_TRACKING_URI", self.tracking_uri)
            os.environ.setdefault("MLFLOW_REGISTRY_URI", self.registry_uri)
            os.environ.setdefault("MLFLOW_EXPERIMENT_ID", self.experiment_id)
