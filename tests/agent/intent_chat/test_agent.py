"""Tests for intent chat agent.

This agent orchestrates the chat workflow using LangGraph.
"""

import pytest
from unittest.mock import MagicMock, AsyncMock


class TestAgent:
    """Tests for Agent that orchestrates the chat workflow."""

    def test_agent_initializes_with_nodes(self):
        """Agent should initialize with all required nodes."""
        from agent_will_smith.agent.intent_chat.agent import Agent

        mock_conversation_node = MagicMock()
        mock_tool_calling_node = MagicMock()
        mock_tool_execution_node = MagicMock()
        mock_response_node = MagicMock()
        mock_config = MagicMock()
        mock_config.agent_timeout_seconds = 120

        agent = Agent(
            conversation_node=mock_conversation_node,
            tool_calling_node=mock_tool_calling_node,
            tool_execution_node=mock_tool_execution_node,
            response_node=mock_response_node,
            agent_config=mock_config,
        )

        assert agent is not None
        assert hasattr(agent, "graph")

    def test_agent_has_invoke_method(self):
        """Agent should have an async invoke method."""
        from agent_will_smith.agent.intent_chat.agent import Agent

        mock_conversation_node = MagicMock()
        mock_tool_calling_node = MagicMock()
        mock_tool_execution_node = MagicMock()
        mock_response_node = MagicMock()
        mock_config = MagicMock()
        mock_config.agent_timeout_seconds = 120

        agent = Agent(
            conversation_node=mock_conversation_node,
            tool_calling_node=mock_tool_calling_node,
            tool_execution_node=mock_tool_execution_node,
            response_node=mock_response_node,
            agent_config=mock_config,
        )

        assert hasattr(agent, "invoke")
        assert callable(agent.invoke)

    @pytest.mark.asyncio
    async def test_agent_invoke_returns_chat_output(self):
        """Agent invoke should return ChatOutput."""
        from agent_will_smith.agent.intent_chat.agent import Agent
        from agent_will_smith.agent.intent_chat.state import (
            ChatInput,
            ChatOutput,
            IntentProfile,
        )
        from agent_will_smith.agent.intent_chat.model.namespaces import (
            ConversationNodeNamespace,
            ToolCallingNodeNamespace,
            ToolExecutionNodeNamespace,
            ResponseNodeNamespace,
        )

        # Create mock nodes that return proper state updates
        mock_conversation_node = MagicMock()
        mock_conversation_node.return_value = {
            "messages": [{"role": "user", "content": "Hello"}],
            "conversation_node": ConversationNodeNamespace(messages_added=1, tokens_used=10),
        }

        mock_tool_calling_node = AsyncMock()
        mock_tool_calling_node.return_value = {
            "current_tool_calls": [],
            "tool_calling_node": ToolCallingNodeNamespace(tool_calls=[]),
            "messages": [
                {"role": "user", "content": "Hello"},
                {"role": "assistant", "content": "Hi there!"},
            ],
        }

        mock_tool_execution_node = AsyncMock()
        mock_tool_execution_node.return_value = {
            "tool_execution_node": ToolExecutionNodeNamespace(tool_results=[]),
        }

        mock_response_node = MagicMock()
        mock_response_node.return_value = {
            "output": ChatOutput(
                response="Hi there!",
                intent_profile=IntentProfile(),
                tool_calls=[],
                session_id="550e8400-e29b-41d4-a716-446655440000",
                is_complete=True,
            ),
            "response_node": ResponseNodeNamespace(response_text="Hi there!", is_streaming=False),
        }

        mock_config = MagicMock()
        mock_config.agent_timeout_seconds = 120
        mock_config.agent_name = "intent_chat"
        mock_config.agent_version = "1.0.0"

        agent = Agent(
            conversation_node=mock_conversation_node,
            tool_calling_node=mock_tool_calling_node,
            tool_execution_node=mock_tool_execution_node,
            response_node=mock_response_node,
            agent_config=mock_config,
        )

        chat_input = ChatInput(
            message="Hello",
            session_id="550e8400-e29b-41d4-a716-446655440000",
        )

        output = await agent.invoke(chat_input)

        assert isinstance(output, ChatOutput)
        assert output.response == "Hi there!"
        assert output.session_id == "550e8400-e29b-41d4-a716-446655440000"

    @pytest.mark.asyncio
    async def test_agent_invoke_raises_timeout_error(self):
        """Agent should raise AgentTimeoutError when execution exceeds timeout."""
        from agent_will_smith.agent.intent_chat.agent import Agent
        from agent_will_smith.agent.intent_chat.state import ChatInput
        from agent_will_smith.agent.intent_chat.model.namespaces import (
            ConversationNodeNamespace,
        )
        from agent_will_smith.core.exceptions import AgentTimeoutError
        import asyncio

        # Create a node that takes too long
        async def slow_node(*args, **kwargs):
            await asyncio.sleep(10)  # Simulate slow operation
            return {}

        mock_conversation_node = MagicMock()
        mock_conversation_node.return_value = {
            "messages": [],
            "conversation_node": ConversationNodeNamespace(messages_added=0, tokens_used=0),
        }

        mock_tool_calling_node = slow_node  # This will timeout

        mock_tool_execution_node = AsyncMock()
        mock_response_node = MagicMock()

        mock_config = MagicMock()
        mock_config.agent_timeout_seconds = 0.1  # Very short timeout
        mock_config.agent_name = "intent_chat"
        mock_config.agent_version = "1.0.0"

        agent = Agent(
            conversation_node=mock_conversation_node,
            tool_calling_node=mock_tool_calling_node,
            tool_execution_node=mock_tool_execution_node,
            response_node=mock_response_node,
            agent_config=mock_config,
        )

        chat_input = ChatInput(
            message="Hello",
            session_id="550e8400-e29b-41d4-a716-446655440000",
        )

        with pytest.raises(AgentTimeoutError):
            await agent.invoke(chat_input)
