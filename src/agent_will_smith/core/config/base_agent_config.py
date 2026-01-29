"""Base configuration for agents with common metadata.

This module provides the BaseAgentConfig class that should be inherited by all
agent-specific configuration classes. It centralizes common fields like agent
identity and prompt caching configuration.
"""

from pydantic import Field
from pydantic_settings import BaseSettings

from agent_will_smith.core.config.validators import SemVer

class BaseAgentConfig(BaseSettings):
    """Base configuration with common agent metadata.

    This base class provides agent identity and prompt caching configuration
    that should be inherited by all agent-specific config classes.

    Note: prompt_name is NOT included here since agents can have multiple prompts.
    Each agent should define its own prompt_name field(s) as needed.
    """

    # Agent Identity
    agent_name: str = Field(..., description="Agent identifier")
    agent_version: SemVer = Field(..., description="Agent version")

    # Prompt Cache Configuration (shared across all prompts in the agent)
    prompt_cache_ttl: int = Field(
        ...,
        description="Prompt cache TTL in seconds for all prompts",
        gt=0
    )
