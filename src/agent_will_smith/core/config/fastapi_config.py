from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from agent_will_smith.core.config.validators import SemVer

class FastAPIConfig(BaseSettings):
    """FastAPI server and application configuration."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="CORE_FASTAPI_",
        case_sensitive=False,
    )

    app_name: str = Field(default="agent-will-smith", description="Application name")
    app_version: SemVer = Field(..., description="Application version")
    enable_docs: bool = Field(default=False, description="Enable API documentation")
    port: int = Field(default=8000, description="API port")
    api_key: str = Field(
        ...,
        description="API key for Bearer token authentication",
    )

