"""Product recommendation agent configuration.

Agent-specific settings for LLM, vector search, and agent behavior.
"""

from pydantic import Field
from pydantic_settings import SettingsConfigDict

from src.agent_will_smith.core.config.base_agent_config import BaseAgentConfig


class ProductRecommendationAgentConfig(BaseAgentConfig):
    """Configuration for product recommendation agent."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="AGENT_PRODUCT_RECOMMENDATION_",
        case_sensitive=False,
        extra="ignore",
    )

    # LLM Configuration
    llm_endpoint: str = Field(..., description="Databricks LLM endpoint name")
    llm_temperature: float = Field(default=1.0, description="LLM temperature", ge=0.0, le=2.0)
    llm_max_tokens: int = Field(..., description="Max tokens for LLM response")

    # Vector Search
    vector_search_endpoint: str = Field(..., description="Databricks vector search endpoint name")
    activities_index: str = Field(..., description="Databricks vector search index for activities")
    books_index: str = Field(..., description="Databricks vector search index for books")
    articles_index: str = Field(..., description="Databricks vector search index for articles")

    # Timeout Configuration
    vector_search_timeout_seconds: float = Field(
        default=5.0,
        description="Timeout for vector search operations per vertical (seconds)",
        ge=0.1,
        le=60.0
    )

    # Agent Behavior
    max_k_products: int = Field(default=10, description="Maximum number of products to return")
    max_agent_steps: int = Field(default=10, description="Maximum agent reasoning steps")
    agent_timeout_seconds: int = Field(default=60, description="Agent execution timeout in seconds")

    # Prompt Management
    prompt_name: str = Field(..., description="MLflow prompt registry path")
