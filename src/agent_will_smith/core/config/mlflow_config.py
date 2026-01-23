from typing import Optional
from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class MLFlowConfig(BaseSettings):
    """MLFlow tracking and registry configuration.
    
    Configuration is validated here and applied in main.py via explicit API calls.
    No global state modification - follows the pattern of other infrastructure clients.
    """

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
        """Validate that tracking URI or experiment ID is provided if tracing is enabled."""
        if self.enable_tracing and not (self.tracking_uri or self.experiment_id):
            raise ValueError(
                "Enable tracing requires at least tracking_uri or experiment_id. "
                "Set CORE_MLFLOW_TRACKING_URI=databricks and CORE_MLFLOW_EXPERIMENT_ID=/path/to/experiment"
            )
        return self
