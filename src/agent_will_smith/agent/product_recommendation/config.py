"""Product recommendation agent configuration.

Agent-specific settings for LLM, vector search, and agent behavior.
"""

from pydantic import Field
from pydantic_settings import SettingsConfigDict

from agent_will_smith.core.config.base_agent_config import BaseAgentConfig


class Config(BaseAgentConfig):
    """Configuration for product recommendation agent."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="AGENT_PRODUCT_RECOMMENDATION_",
        case_sensitive=False,
        extra="ignore",
    )

    # LLM Configuration
    llm_endpoint: str = Field(
        ...,
        description="Databricks LLM endpoint name",
        min_length=1,
        max_length=200,
        examples=["databricks-gpt-4-mini"],
    )
    llm_temperature: float = Field(
        default=1.0,
        description="LLM temperature",
        ge=0.0,
        le=2.0,
    )
    llm_max_tokens: int = Field(
        ...,
        description="Max tokens for LLM response",
        ge=1,
        le=100000,
        examples=[4000],
    )

    # Vector Search - unified indices configuration
    vector_search_endpoint: str = Field(
        ...,
        description="Databricks vector search endpoint name",
        min_length=1,
        max_length=200,
        examples=["vector-search-endpoint"],
    )
    product_indices: dict[str, str] = Field(
        ...,
        description="Mapping of product verticals to vector search index names",
        examples=[{
            "activities": "catalog.schema.content_activity_gold_index",
            "books": "catalog.schema.content_book_gold_index",
            "articles": "catalog.schema.content_article_gold_index",
        }],
    )

    # Timeout Configuration
    vector_search_timeout_seconds: float = Field(
        default=5.0,
        description="Timeout for vector search operations per vertical (seconds)",
        ge=0.1,
        le=60.0
    )

    # Agent Behavior
    agent_timeout_seconds: int = Field(default=60, description="Agent execution timeout in seconds")

    # Prompt Management
    prompt_name: str = Field(
        ...,
        description="MLflow prompt registry path (format: prompts:/catalog.schema.name/version)",
        min_length=1,
        max_length=500,
        pattern=r"^prompts:/[\w./]+$",
        examples=["prompts:/main.default.intent_analysis/1"],
    )
