from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class GeminiConfig(BaseSettings):
    """Gemini configuration for embedding."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="CORE_GEMINI_",
        case_sensitive=False,
    )

    api_key: str = Field(..., description="Gemini API key", repr=False)
    embedding_model: str = Field(..., description="Gemini embedding model name")
    embedding_dimension: int = Field(..., description="Output dimension for embeddings")
