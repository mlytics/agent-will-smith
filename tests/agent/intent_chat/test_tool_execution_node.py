"""Tests for tool execution node.

This node executes the tool calls from tool_calling_node.
"""

import pytest
from unittest.mock import MagicMock, AsyncMock, patch


class TestToolExecutionNode:
    """Tests for ToolExecutionNode that executes tool calls."""

    def test_node_is_callable(self):
        """Node should be a callable class with __call__ method."""
        from agent_will_smith.agent.intent_chat.node.tool_execution_node import (
            ToolExecutionNode,
        )

        mock_config = MagicMock()
        mock_config.tool_timeout_seconds = 30

        node = ToolExecutionNode(config=mock_config)
        assert callable(node)

    @pytest.mark.asyncio
    async def test_node_executes_tool_and_returns_results(self):
        """Node should execute tool calls and return results."""
        from agent_will_smith.agent.intent_chat.node.tool_execution_node import (
            ToolExecutionNode,
        )
        from agent_will_smith.agent.intent_chat.state import ChatState, ChatInput

        mock_config = MagicMock()
        mock_config.tool_timeout_seconds = 30

        node = ToolExecutionNode(config=mock_config)

        chat_input = ChatInput(
            message="What is my risk tolerance?",
            session_id="550e8400-e29b-41d4-a716-446655440000",
        )
        state = ChatState(
            input=chat_input,
            messages=[{"role": "user", "content": "What is my risk tolerance?"}],
            current_tool_calls=[
                {
                    "id": "call_123",
                    "name": "clarification",
                    "args": {
                        "question": "What is your risk tolerance?",
                        "options": ["Low", "Medium", "High"],
                    },
                }
            ],
        )

        result = await node(state)

        assert "tool_execution_node" in result
        assert len(result["tool_execution_node"].tool_results) == 1
        tool_result = result["tool_execution_node"].tool_results[0]
        assert tool_result.tool_call_id == "call_123"
        assert tool_result.result is not None

    @pytest.mark.asyncio
    async def test_node_handles_tool_errors_gracefully(self):
        """Node should capture errors when tool execution fails."""
        from agent_will_smith.agent.intent_chat.node.tool_execution_node import (
            ToolExecutionNode,
        )
        from agent_will_smith.agent.intent_chat.state import ChatState, ChatInput

        mock_config = MagicMock()
        mock_config.tool_timeout_seconds = 30

        node = ToolExecutionNode(config=mock_config)

        chat_input = ChatInput(
            message="Test",
            session_id="550e8400-e29b-41d4-a716-446655440000",
        )
        state = ChatState(
            input=chat_input,
            messages=[{"role": "user", "content": "Test"}],
            current_tool_calls=[
                {
                    "id": "call_456",
                    "name": "unknown_tool",  # Unknown tool should error
                    "args": {},
                }
            ],
        )

        result = await node(state)

        assert "tool_execution_node" in result
        tool_result = result["tool_execution_node"].tool_results[0]
        assert tool_result.error is not None
        assert "unknown_tool" in tool_result.error.lower() or "not found" in tool_result.error.lower()

    @pytest.mark.asyncio
    async def test_node_updates_intent_profile_from_intent_capture(self):
        """Node should update intent_profile when intent_capture tool is used."""
        from agent_will_smith.agent.intent_chat.node.tool_execution_node import (
            ToolExecutionNode,
        )
        from agent_will_smith.agent.intent_chat.state import ChatState, ChatInput, IntentProfile

        mock_config = MagicMock()
        mock_config.tool_timeout_seconds = 30

        node = ToolExecutionNode(config=mock_config)

        chat_input = ChatInput(
            message="I want to retire comfortably",
            session_id="550e8400-e29b-41d4-a716-446655440000",
        )
        state = ChatState(
            input=chat_input,
            messages=[{"role": "user", "content": "I want to retire comfortably"}],
            intent_profile=IntentProfile(intent_score=0.3),
            current_tool_calls=[
                {
                    "id": "call_789",
                    "name": "intent_capture",
                    "args": {
                        "category": "retirement",
                        "signal_type": "explicit",
                        "confidence": 0.9,
                    },
                }
            ],
        )

        result = await node(state)

        # Intent profile should be updated with new signal
        assert "intent_profile" in result
        updated_profile = result["intent_profile"]
        assert len(updated_profile.signals) == 1
        assert updated_profile.signals[0].category == "retirement"

    @pytest.mark.asyncio
    async def test_node_returns_empty_results_when_no_tool_calls(self):
        """Node should return empty results when there are no tool calls."""
        from agent_will_smith.agent.intent_chat.node.tool_execution_node import (
            ToolExecutionNode,
        )
        from agent_will_smith.agent.intent_chat.state import ChatState, ChatInput

        mock_config = MagicMock()
        mock_config.tool_timeout_seconds = 30

        node = ToolExecutionNode(config=mock_config)

        chat_input = ChatInput(
            message="Hello",
            session_id="550e8400-e29b-41d4-a716-446655440000",
        )
        state = ChatState(
            input=chat_input,
            messages=[{"role": "user", "content": "Hello"}],
            current_tool_calls=[],
        )

        result = await node(state)

        assert "tool_execution_node" in result
        assert len(result["tool_execution_node"].tool_results) == 0


class TestUpdateIntentProfile:
    """Tests for _update_intent_profile method with new extended fields."""

    def test_update_with_life_stage(self):
        """Test updating profile with life_stage from signal."""
        from agent_will_smith.agent.intent_chat.node.tool_execution_node import (
            ToolExecutionNode,
        )
        from agent_will_smith.agent.intent_chat.state import IntentProfile

        mock_config = MagicMock()
        node = ToolExecutionNode(config=mock_config)
        current = IntentProfile()
        signals = [{
            "type": "intent_signal",
            "category": "retirement",
            "signal_type": "explicit",
            "confidence": 0.9,
            "life_stage": "pre_retirement",
        }]

        updated = node._update_intent_profile(current, signals)

        assert updated.life_stage == "pre_retirement"

    def test_update_with_risk_preference(self):
        """Test updating profile with risk_preference from signal."""
        from agent_will_smith.agent.intent_chat.node.tool_execution_node import (
            ToolExecutionNode,
        )
        from agent_will_smith.agent.intent_chat.state import IntentProfile

        mock_config = MagicMock()
        node = ToolExecutionNode(config=mock_config)
        current = IntentProfile()
        signals = [{
            "type": "intent_signal",
            "category": "investment",
            "signal_type": "explicit",
            "confidence": 0.85,
            "risk_preference": "aggressive",
        }]

        updated = node._update_intent_profile(current, signals)

        assert updated.risk_preference == "aggressive"

    def test_update_with_financial_goal(self):
        """Test updating profile with financial goal fields from signal."""
        from agent_will_smith.agent.intent_chat.node.tool_execution_node import (
            ToolExecutionNode,
        )
        from agent_will_smith.agent.intent_chat.state import IntentProfile

        mock_config = MagicMock()
        node = ToolExecutionNode(config=mock_config)
        current = IntentProfile()
        signals = [{
            "type": "intent_signal",
            "category": "retirement",
            "signal_type": "explicit",
            "confidence": 0.9,
            "target_age": 50,
            "target_amount": "2000萬",
            "timeline": "5年",
            "goal_type": "retirement",
        }]

        updated = node._update_intent_profile(current, signals)

        assert updated.financial_goal is not None
        assert updated.financial_goal.target_age == 50
        assert updated.financial_goal.target_amount == "2000萬"
        assert updated.financial_goal.timeline == "5年"
        assert updated.financial_goal.goal_type == "retirement"

    def test_update_with_assets_and_experience(self):
        """Test updating profile with current_assets and investment_experience."""
        from agent_will_smith.agent.intent_chat.node.tool_execution_node import (
            ToolExecutionNode,
        )
        from agent_will_smith.agent.intent_chat.state import IntentProfile

        mock_config = MagicMock()
        node = ToolExecutionNode(config=mock_config)
        current = IntentProfile()
        signals = [{
            "type": "intent_signal",
            "category": "investment",
            "signal_type": "explicit",
            "confidence": 0.8,
            "current_assets": "1000萬台幣",
            "investment_experience": "intermediate",
        }]

        updated = node._update_intent_profile(current, signals)

        assert updated.current_assets == "1000萬台幣"
        assert updated.investment_experience == "intermediate"

    def test_preserves_existing_values(self):
        """Test that existing profile values are preserved if not in signal."""
        from agent_will_smith.agent.intent_chat.node.tool_execution_node import (
            ToolExecutionNode,
        )
        from agent_will_smith.agent.intent_chat.state import IntentProfile

        mock_config = MagicMock()
        node = ToolExecutionNode(config=mock_config)
        current = IntentProfile(
            life_stage="mid_career",
            risk_preference="moderate",
        )
        signals = [{
            "type": "intent_signal",
            "category": "retirement",
            "signal_type": "explicit",
            "confidence": 0.9,
            "target_age": 55,
        }]

        updated = node._update_intent_profile(current, signals)

        assert updated.life_stage == "mid_career"  # Preserved
        assert updated.risk_preference == "moderate"  # Preserved
        assert updated.financial_goal.target_age == 55  # Updated

    def test_updates_signal_from_new_values_override_none(self):
        """Test that signal values override None in existing profile."""
        from agent_will_smith.agent.intent_chat.node.tool_execution_node import (
            ToolExecutionNode,
        )
        from agent_will_smith.agent.intent_chat.state import IntentProfile

        mock_config = MagicMock()
        node = ToolExecutionNode(config=mock_config)
        current = IntentProfile(
            life_stage=None,
            risk_preference=None,
        )
        signals = [{
            "type": "intent_signal",
            "category": "retirement",
            "signal_type": "explicit",
            "confidence": 0.9,
            "life_stage": "early_career",
            "risk_preference": "conservative",
        }]

        updated = node._update_intent_profile(current, signals)

        assert updated.life_stage == "early_career"
        assert updated.risk_preference == "conservative"
