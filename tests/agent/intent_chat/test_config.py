"""Tests for intent chat agent configuration."""

import os
import pytest
from pydantic import ValidationError


class TestConfig:
    """Tests for Config class validation and defaults."""

    def test_config_loads_with_valid_env_vars(self, monkeypatch):
        """Config should load successfully with all required env vars."""
        # Arrange: Set all required env vars
        monkeypatch.setenv("AGENT_INTENT_CHAT_AGENT_NAME", "intent_chat")
        monkeypatch.setenv("AGENT_INTENT_CHAT_AGENT_VERSION", "1.0.0")
        monkeypatch.setenv("AGENT_INTENT_CHAT_PROMPT_CACHE_TTL", "3600")
        monkeypatch.setenv("AGENT_INTENT_CHAT_LLM_ENDPOINT", "databricks-gpt-5-mini")
        monkeypatch.setenv("AGENT_INTENT_CHAT_SYSTEM_PROMPT_NAME", "prompts:/aigc_prod.intent_engine.intent_chat_system/1")

        # Act
        from agent_will_smith.agent.intent_chat.config import Config
        config = Config()

        # Assert
        assert config.agent_name == "intent_chat"
        assert config.agent_version == "1.0.0"
        assert config.llm_endpoint == "databricks-gpt-5-mini"

    def test_config_uses_correct_env_prefix(self, monkeypatch):
        """Config should use AGENT_INTENT_CHAT_ prefix."""
        # Arrange: Use wrong prefix, should fail
        monkeypatch.setenv("AGENT_PRODUCT_RECOMMENDATION_LLM_ENDPOINT", "wrong-endpoint")
        monkeypatch.setenv("AGENT_INTENT_CHAT_AGENT_NAME", "intent_chat")
        monkeypatch.setenv("AGENT_INTENT_CHAT_AGENT_VERSION", "1.0.0")
        monkeypatch.setenv("AGENT_INTENT_CHAT_PROMPT_CACHE_TTL", "3600")
        monkeypatch.setenv("AGENT_INTENT_CHAT_LLM_ENDPOINT", "correct-endpoint")
        monkeypatch.setenv("AGENT_INTENT_CHAT_SYSTEM_PROMPT_NAME", "prompts:/test/1")

        # Act
        from agent_will_smith.agent.intent_chat.config import Config
        config = Config()

        # Assert: Should use AGENT_INTENT_CHAT_ prefix, not AGENT_PRODUCT_RECOMMENDATION_
        assert config.llm_endpoint == "correct-endpoint"

    def test_config_defaults_for_optional_fields(self, monkeypatch):
        """Config should apply correct defaults for optional fields."""
        # Arrange: Set only required fields
        monkeypatch.setenv("AGENT_INTENT_CHAT_AGENT_NAME", "intent_chat")
        monkeypatch.setenv("AGENT_INTENT_CHAT_AGENT_VERSION", "1.0.0")
        monkeypatch.setenv("AGENT_INTENT_CHAT_PROMPT_CACHE_TTL", "3600")
        monkeypatch.setenv("AGENT_INTENT_CHAT_LLM_ENDPOINT", "databricks-gpt-5-mini")
        monkeypatch.setenv("AGENT_INTENT_CHAT_SYSTEM_PROMPT_NAME", "prompts:/test/1")

        # Act
        from agent_will_smith.agent.intent_chat.config import Config
        config = Config()

        # Assert: Check defaults match plan specification
        assert config.llm_temperature == 0.7
        assert config.llm_max_tokens == 4096
        assert config.max_conversation_turns == 20
        assert config.intent_score_threshold == 0.7
        assert config.agent_timeout_seconds == 120
        assert config.tool_timeout_seconds == 30

    def test_config_fails_without_required_fields(self, monkeypatch):
        """Config should raise ValidationError when required fields are missing."""
        # Arrange: Don't set required fields
        monkeypatch.delenv("AGENT_INTENT_CHAT_LLM_ENDPOINT", raising=False)

        # Act & Assert
        from agent_will_smith.agent.intent_chat.config import Config
        with pytest.raises(ValidationError):
            Config()

    def test_config_validates_llm_temperature_range(self, monkeypatch):
        """Config should validate llm_temperature is between 0.0 and 2.0."""
        # Arrange
        monkeypatch.setenv("AGENT_INTENT_CHAT_AGENT_NAME", "intent_chat")
        monkeypatch.setenv("AGENT_INTENT_CHAT_AGENT_VERSION", "1.0.0")
        monkeypatch.setenv("AGENT_INTENT_CHAT_PROMPT_CACHE_TTL", "3600")
        monkeypatch.setenv("AGENT_INTENT_CHAT_LLM_ENDPOINT", "test-endpoint")
        monkeypatch.setenv("AGENT_INTENT_CHAT_SYSTEM_PROMPT_NAME", "prompts:/test/1")
        monkeypatch.setenv("AGENT_INTENT_CHAT_LLM_TEMPERATURE", "3.0")  # Invalid

        # Act & Assert
        from agent_will_smith.agent.intent_chat.config import Config
        with pytest.raises(ValidationError):
            Config()

    def test_config_validates_intent_score_threshold_range(self, monkeypatch):
        """Config should validate intent_score_threshold is between 0.0 and 1.0."""
        # Arrange
        monkeypatch.setenv("AGENT_INTENT_CHAT_AGENT_NAME", "intent_chat")
        monkeypatch.setenv("AGENT_INTENT_CHAT_AGENT_VERSION", "1.0.0")
        monkeypatch.setenv("AGENT_INTENT_CHAT_PROMPT_CACHE_TTL", "3600")
        monkeypatch.setenv("AGENT_INTENT_CHAT_LLM_ENDPOINT", "test-endpoint")
        monkeypatch.setenv("AGENT_INTENT_CHAT_SYSTEM_PROMPT_NAME", "prompts:/test/1")
        monkeypatch.setenv("AGENT_INTENT_CHAT_INTENT_SCORE_THRESHOLD", "1.5")  # Invalid

        # Act & Assert
        from agent_will_smith.agent.intent_chat.config import Config
        with pytest.raises(ValidationError):
            Config()

    def test_config_validates_system_prompt_name_format(self, monkeypatch):
        """Config should validate system_prompt_name matches prompts:/ pattern."""
        # Arrange
        monkeypatch.setenv("AGENT_INTENT_CHAT_AGENT_NAME", "intent_chat")
        monkeypatch.setenv("AGENT_INTENT_CHAT_AGENT_VERSION", "1.0.0")
        monkeypatch.setenv("AGENT_INTENT_CHAT_PROMPT_CACHE_TTL", "3600")
        monkeypatch.setenv("AGENT_INTENT_CHAT_LLM_ENDPOINT", "test-endpoint")
        monkeypatch.setenv("AGENT_INTENT_CHAT_SYSTEM_PROMPT_NAME", "invalid-format")  # Invalid

        # Act & Assert
        from agent_will_smith.agent.intent_chat.config import Config
        with pytest.raises(ValidationError):
            Config()
