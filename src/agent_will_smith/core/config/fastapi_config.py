from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from semver import Version

class FastAPIConfig(BaseSettings):
    """FastAPI server and application configuration."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="CORE_FASTAPI_",
        case_sensitive=False,
    )

    app_name: str = Field(default="agent-will-smith", description="Application name")
    app_version: str = Field(..., description="Application version")
    enable_docs: bool = Field(default=False, description="Enable API documentation")
    port: int = Field(default=8000, description="API port")
    api_key: str = Field(
        ...,
        description="Bearer token for API authentication",
    )


    @field_validator("app_version", mode="after")
    @classmethod
    def app_version_is_valid(cls, v):
        if not Version.is_valid(v):
            raise ValueError(f"Invalid application version: {v}")
        return v

