from typing import Any, Optional
import os
from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class DatabricksConfig(BaseSettings):
    """Databricks workspace configuration with OAuth authentication."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )

    databricks_host: str = Field(..., description="Databricks workspace URL")
    databricks_client_id: Optional[str] = Field(None, description="Databricks OAuth client ID")
    databricks_client_secret: Optional[str] = Field(
        None, description="Databricks OAuth client secret"
    )
    databricks_config_profile: Optional[str] = Field(None, description="Databricks config profile")

    @model_validator(mode="after")
    def check_auth_config(self) -> "DatabricksConfig":
        """Validate that either OAuth credentials or a config file is provided."""
        if (
            not (self.databricks_client_id and self.databricks_client_secret)
            and not self.databricks_config_profile
        ):
            raise ValueError(
                "Either (databricks_client_id and databricks_client_secret) or databricks_config_profile must be provided."
            )
        return self

    def model_post_init(self, __context: Any) -> None:
        """Set Databricks environment variables for SDK compatibility."""
        os.environ.setdefault("DATABRICKS_HOST", self.databricks_host)
        if self.databricks_client_id and self.databricks_client_secret:
            os.environ.setdefault("DATABRICKS_CLIENT_ID", self.databricks_client_id)
            os.environ.setdefault("DATABRICKS_CLIENT_SECRET", self.databricks_client_secret)
        if self.databricks_config_profile:
            os.environ.setdefault("DATABRICKS_CONFIG_PROFILE", self.databricks_config_profile)
