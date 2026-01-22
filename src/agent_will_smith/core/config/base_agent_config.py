"""Base configuration for agents with common metadata.

This module provides the BaseAgentConfig class that should be inherited by all
agent-specific configuration classes. It centralizes common fields like agent
identity and prompt caching configuration.
"""

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from semver import Version

class BaseAgentConfig(BaseSettings):
    model_config = SettingsConfigDict(extra="ignore")
    """Base configuration with common agent metadata.

    This base class provides agent identity and prompt caching configuration
    that should be inherited by all agent-specific config classes.

    Note: prompt_name is NOT included here since agents can have multiple prompts.
    Each agent should define its own prompt_name field(s) as needed.
    """

    # Agent Identity
    agent_name: str = Field(..., description="Agent identifier")
    agent_version: str = Field(..., description="Agent version")

    # Prompt Cache Configuration (shared across all prompts in the agent)
    prompt_cache_ttl: int = Field(
        ...,
        description="Prompt cache TTL in seconds for all prompts",
        gt=0
    )

    @field_validator("agent_version", mode="after")
    @classmethod
    def agent_version_is_valid(cls, v):
        if not Version.is_valid(v):
            raise ValueError(f"Invalid agent version: {v}")
        return v
