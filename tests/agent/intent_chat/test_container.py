"""Tests for intent chat container.

This container wires all dependencies for the intent chat agent.
"""

import pytest
from unittest.mock import MagicMock, patch


class TestContainer:
    """Tests for Container that wires intent chat dependencies."""

    def test_container_has_agent_config_provider(self):
        """Container should have agent_config provider."""
        from agent_will_smith.agent.intent_chat.container import Container

        container = Container()
        assert hasattr(container, "agent_config")

    def test_container_has_node_providers(self):
        """Container should have providers for all 4 nodes."""
        from agent_will_smith.agent.intent_chat.container import Container

        container = Container()
        assert hasattr(container, "conversation_node")
        assert hasattr(container, "tool_calling_node")
        assert hasattr(container, "tool_execution_node")
        assert hasattr(container, "response_node")

    def test_container_has_agent_provider(self):
        """Container should have agent provider."""
        from agent_will_smith.agent.intent_chat.container import Container

        container = Container()
        assert hasattr(container, "agent")

    @patch.dict(
        "os.environ",
        {
            "AGENT_INTENT_CHAT_AGENT_NAME": "intent_chat",
            "AGENT_INTENT_CHAT_AGENT_VERSION": "1.0.0",
            "AGENT_INTENT_CHAT_PROMPT_CACHE_TTL": "3600",
            "AGENT_INTENT_CHAT_LLM_ENDPOINT": "databricks-gpt-5-mini",
            "AGENT_INTENT_CHAT_SYSTEM_PROMPT_NAME": "prompts:/test.prompt/1",
        },
    )
    def test_container_agent_config_loads_from_env(self):
        """Container agent_config should load from environment variables."""
        from agent_will_smith.agent.intent_chat.container import Container
        from agent_will_smith.agent.intent_chat.config import Config

        container = Container()
        config = container.agent_config()

        assert isinstance(config, Config)
        assert config.llm_endpoint == "databricks-gpt-5-mini"

    @patch.dict(
        "os.environ",
        {
            "AGENT_INTENT_CHAT_AGENT_NAME": "intent_chat",
            "AGENT_INTENT_CHAT_AGENT_VERSION": "1.0.0",
            "AGENT_INTENT_CHAT_PROMPT_CACHE_TTL": "3600",
            "AGENT_INTENT_CHAT_LLM_ENDPOINT": "databricks-gpt-5-mini",
            "AGENT_INTENT_CHAT_SYSTEM_PROMPT_NAME": "prompts:/test.prompt/1",
        },
    )
    def test_container_provides_configured_nodes(self):
        """Container should provide properly configured nodes."""
        from agent_will_smith.agent.intent_chat.container import Container
        from agent_will_smith.agent.intent_chat.node.conversation_node import ConversationNode
        from agent_will_smith.agent.intent_chat.node.tool_calling_node import ToolCallingNode
        from agent_will_smith.agent.intent_chat.node.tool_execution_node import ToolExecutionNode
        from agent_will_smith.agent.intent_chat.node.response_node import ResponseNode

        # Mock the infra container's clients to avoid actual client creation
        with patch("agent_will_smith.agent.intent_chat.container.InfraContainer") as mock_infra:
            mock_llm_client = MagicMock()
            mock_prompt_client = MagicMock()
            mock_infra.return_value.llm_client.return_value = mock_llm_client
            mock_infra.return_value.prompt_client.return_value = mock_prompt_client

            container = Container()

            # Verify nodes are created with correct types
            conversation_node = container.conversation_node()
            tool_calling_node = container.tool_calling_node()
            tool_execution_node = container.tool_execution_node()
            response_node = container.response_node()

            assert isinstance(conversation_node, ConversationNode)
            assert isinstance(tool_calling_node, ToolCallingNode)
            assert isinstance(tool_execution_node, ToolExecutionNode)
            assert isinstance(response_node, ResponseNode)

    @patch.dict(
        "os.environ",
        {
            "AGENT_INTENT_CHAT_AGENT_NAME": "intent_chat",
            "AGENT_INTENT_CHAT_AGENT_VERSION": "1.0.0",
            "AGENT_INTENT_CHAT_PROMPT_CACHE_TTL": "3600",
            "AGENT_INTENT_CHAT_LLM_ENDPOINT": "databricks-gpt-5-mini",
            "AGENT_INTENT_CHAT_SYSTEM_PROMPT_NAME": "prompts:/test.prompt/1",
        },
    )
    def test_container_provides_agent_with_all_nodes(self):
        """Container agent should be wired with all nodes."""
        from agent_will_smith.agent.intent_chat.container import Container
        from agent_will_smith.agent.intent_chat.agent import Agent

        # Mock the infra container's clients
        with patch("agent_will_smith.agent.intent_chat.container.InfraContainer") as mock_infra:
            mock_llm_client = MagicMock()
            mock_prompt_client = MagicMock()
            mock_infra.return_value.llm_client.return_value = mock_llm_client
            mock_infra.return_value.prompt_client.return_value = mock_prompt_client

            container = Container()
            agent = container.agent()

            assert isinstance(agent, Agent)
            assert hasattr(agent, "graph")
