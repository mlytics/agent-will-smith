"""Tests for tool calling node.

This node uses LLM with bound tools to decide what actions to take.
"""

import pytest
from unittest.mock import MagicMock, AsyncMock


class TestToolCallingNode:
    """Tests for ToolCallingNode that decides tool invocations."""

    def test_node_is_callable(self):
        """Node should be a callable class with __call__ method."""
        from agent_will_smith.agent.intent_chat.node.tool_calling_node import (
            ToolCallingNode,
        )

        mock_llm = MagicMock()
        mock_prompt_client = MagicMock()
        mock_config = MagicMock()
        mock_config.system_prompt_name = "prompts:/test/1"

        node = ToolCallingNode(
            llm_client=mock_llm,
            prompt_client=mock_prompt_client,
            config=mock_config,
        )
        assert callable(node)

    @pytest.mark.asyncio
    async def test_node_returns_tool_calls_when_llm_decides(self):
        """Node should return tool calls when LLM decides to use tools."""
        from agent_will_smith.agent.intent_chat.node.tool_calling_node import (
            ToolCallingNode,
        )
        from agent_will_smith.agent.intent_chat.state import ChatState, ChatInput
        from agent_will_smith.agent.intent_chat.model.namespaces import ToolCall

        # Mock LLM that returns tool calls
        mock_response = MagicMock()
        mock_response.tool_calls = [
            {
                "id": "call_123",
                "name": "clarification",
                "args": {"question": "What is your risk tolerance?", "options": ["Low", "Medium", "High"]},
            }
        ]
        mock_response.content = ""

        mock_llm = MagicMock()
        mock_llm.bind_tools = MagicMock(return_value=mock_llm)
        mock_llm.ainvoke = AsyncMock(return_value=mock_response)

        mock_prompt_client = MagicMock()
        mock_prompt_client.load_prompt = MagicMock(return_value="You are a helpful assistant.")

        mock_config = MagicMock()
        mock_config.system_prompt_name = "prompts:/test/1"
        mock_config.intent_score_threshold = 0.7

        node = ToolCallingNode(
            llm_client=mock_llm,
            prompt_client=mock_prompt_client,
            config=mock_config,
        )

        chat_input = ChatInput(
            message="I want to invest",
            session_id="550e8400-e29b-41d4-a716-446655440000",
        )
        state = ChatState(
            input=chat_input,
            messages=[{"role": "user", "content": "I want to invest"}],
        )

        result = await node(state)

        assert "tool_calling_node" in result
        assert "current_tool_calls" in result
        assert len(result["current_tool_calls"]) == 1
        assert result["current_tool_calls"][0]["name"] == "clarification"

    @pytest.mark.asyncio
    async def test_node_returns_empty_tool_calls_when_no_tools_needed(self):
        """Node should return empty tool_calls when LLM responds with text only."""
        from agent_will_smith.agent.intent_chat.node.tool_calling_node import (
            ToolCallingNode,
        )
        from agent_will_smith.agent.intent_chat.state import ChatState, ChatInput

        # Mock LLM that returns text only (no tool calls)
        mock_response = MagicMock()
        mock_response.tool_calls = []
        mock_response.content = "Hello! How can I help you today?"

        mock_llm = MagicMock()
        mock_llm.bind_tools = MagicMock(return_value=mock_llm)
        mock_llm.ainvoke = AsyncMock(return_value=mock_response)

        mock_prompt_client = MagicMock()
        mock_prompt_client.load_prompt = MagicMock(return_value="You are a helpful assistant.")

        mock_config = MagicMock()
        mock_config.system_prompt_name = "prompts:/test/1"
        mock_config.intent_score_threshold = 0.7

        node = ToolCallingNode(
            llm_client=mock_llm,
            prompt_client=mock_prompt_client,
            config=mock_config,
        )

        chat_input = ChatInput(
            message="Hello",
            session_id="550e8400-e29b-41d4-a716-446655440000",
        )
        state = ChatState(
            input=chat_input,
            messages=[{"role": "user", "content": "Hello"}],
        )

        result = await node(state)

        assert "current_tool_calls" in result
        assert len(result["current_tool_calls"]) == 0

    @pytest.mark.asyncio
    async def test_node_includes_intent_profile_in_context(self):
        """Node should include intent profile in LLM context for better decisions."""
        from agent_will_smith.agent.intent_chat.node.tool_calling_node import (
            ToolCallingNode,
        )
        from agent_will_smith.agent.intent_chat.state import ChatState, ChatInput, IntentProfile

        mock_response = MagicMock()
        mock_response.tool_calls = []
        mock_response.content = "I understand you're interested in retirement."

        mock_llm = MagicMock()
        mock_llm.bind_tools = MagicMock(return_value=mock_llm)
        mock_llm.ainvoke = AsyncMock(return_value=mock_response)

        mock_prompt_client = MagicMock()
        mock_prompt_client.load_prompt = MagicMock(return_value="System prompt")

        mock_config = MagicMock()
        mock_config.system_prompt_name = "prompts:/test/1"
        mock_config.intent_score_threshold = 0.7

        node = ToolCallingNode(
            llm_client=mock_llm,
            prompt_client=mock_prompt_client,
            config=mock_config,
        )

        chat_input = ChatInput(
            message="Tell me more",
            session_id="550e8400-e29b-41d4-a716-446655440000",
        )
        intent_profile = IntentProfile(
            life_stage="mid_career",
            intent_score=0.6,
            product_interests=["retirement"],
        )
        state = ChatState(
            input=chat_input,
            messages=[{"role": "user", "content": "Tell me more"}],
            intent_profile=intent_profile,
        )

        await node(state)

        # Verify LLM was called with messages
        mock_llm.ainvoke.assert_called_once()
