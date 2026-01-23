"""Intent chat agent configuration.

Agent-specific settings for LLM, conversation management, and tool execution.
"""

from pydantic import Field
from pydantic_settings import SettingsConfigDict

from agent_will_smith.core.config.base_agent_config import BaseAgentConfig


class Config(BaseAgentConfig):
    """Configuration for intent chat agent."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="AGENT_INTENT_CHAT_",
        case_sensitive=False,
        extra="ignore",
    )

    # LLM Configuration
    llm_endpoint: str = Field(
        ...,
        description="Databricks LLM endpoint name for chat completions",
        min_length=1,
        max_length=200,
        examples=["databricks-gpt-4-mini"],
    )
    llm_temperature: float = Field(
        default=0.7,
        description="LLM temperature for response generation",
        ge=0.0,
        le=2.0,
    )
    llm_max_tokens: int = Field(
        default=4096,
        description="Maximum tokens for LLM response",
        ge=1,
        le=100000,
        examples=[4096],
    )

    # Prompt Management
    system_prompt_name: str = Field(
        ...,
        description="MLflow prompt registry path for chat system prompt (format: prompts:/catalog.schema.name/version)",
        min_length=1,
        max_length=500,
        pattern=r"^prompts:/[\w./]+$",
        examples=["prompts:/main.default.intent_chat_system/1"],
    )

    # Conversation Management
    max_conversation_turns: int = Field(
        default=20,
        description="Maximum number of conversation turns before requiring reset",
        ge=1,
        le=100,
    )

    # Intent Detection
    intent_score_threshold: float = Field(
        default=0.7,
        description="Minimum intent score (0.0-1.0) to trigger product recommendation tool",
        ge=0.0,
        le=1.0,
    )

    # Timeout Configuration
    agent_timeout_seconds: int = Field(
        default=120,
        description="Overall agent execution timeout in seconds",
        ge=1,
        le=600,
    )
    tool_timeout_seconds: int = Field(
        default=30,
        description="Timeout for individual tool executions in seconds",
        ge=1,
        le=300,
    )

    # Analytics Configuration
    analytics_db_path: str = Field(
        default="/tmp/conversation_analytics.db",
        description="Path to SQLite database for conversation analytics",
    )
    analytics_enabled: bool = Field(
        default=True,
        description="Enable conversation analytics logging",
    )
