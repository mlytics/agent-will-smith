"""Tests for response node.

This node composes the final ChatOutput from the state.
"""

import pytest


class TestResponseNode:
    """Tests for ResponseNode that composes final output."""

    def test_node_is_callable(self):
        """Node should be a callable class with __call__ method."""
        from agent_will_smith.agent.intent_chat.node.response_node import (
            ResponseNode,
        )

        node = ResponseNode()
        assert callable(node)

    def test_node_creates_chat_output_from_state(self):
        """Node should create ChatOutput from state with all fields."""
        from agent_will_smith.agent.intent_chat.node.response_node import (
            ResponseNode,
        )
        from agent_will_smith.agent.intent_chat.state import (
            ChatState,
            ChatInput,
            ChatOutput,
            IntentProfile,
        )
        from agent_will_smith.agent.intent_chat.model.namespaces import (
            ResponseNodeNamespace,
            ToolExecutionNodeNamespace,
            ToolResult,
        )

        node = ResponseNode()

        chat_input = ChatInput(
            message="Hello",
            session_id="550e8400-e29b-41d4-a716-446655440000",
        )
        state = ChatState(
            input=chat_input,
            messages=[
                {"role": "user", "content": "Hello"},
                {"role": "assistant", "content": "Hi! How can I help you today?"},
            ],
            intent_profile=IntentProfile(intent_score=0.5),
            tool_execution_node=ToolExecutionNodeNamespace(tool_results=[]),
        )

        result = node(state)

        assert "output" in result
        assert "response_node" in result
        output = result["output"]
        assert isinstance(output, ChatOutput)
        assert output.response == "Hi! How can I help you today?"
        assert output.session_id == "550e8400-e29b-41d4-a716-446655440000"
        assert output.is_complete is True

    def test_node_includes_tool_calls_in_output(self):
        """Node should include tool call results in output."""
        from agent_will_smith.agent.intent_chat.node.response_node import (
            ResponseNode,
        )
        from agent_will_smith.agent.intent_chat.state import (
            ChatState,
            ChatInput,
            IntentProfile,
        )
        from agent_will_smith.agent.intent_chat.model.namespaces import (
            ToolExecutionNodeNamespace,
            ToolResult,
        )

        node = ResponseNode()

        chat_input = ChatInput(
            message="What should I invest in?",
            session_id="550e8400-e29b-41d4-a716-446655440000",
        )
        state = ChatState(
            input=chat_input,
            messages=[
                {"role": "user", "content": "What should I invest in?"},
                {"role": "assistant", "content": "Let me clarify your preferences."},
            ],
            intent_profile=IntentProfile(),
            tool_execution_node=ToolExecutionNodeNamespace(
                tool_results=[
                    ToolResult(
                        tool_call_id="call_123",
                        result={"type": "clarification", "question": "What is your risk level?"},
                        error=None,
                    )
                ]
            ),
        )

        result = node(state)

        output = result["output"]
        assert len(output.tool_calls) == 1
        assert output.tool_calls[0]["tool_call_id"] == "call_123"

    def test_node_uses_latest_assistant_message_as_response(self):
        """Node should use the last assistant message as the response."""
        from agent_will_smith.agent.intent_chat.node.response_node import (
            ResponseNode,
        )
        from agent_will_smith.agent.intent_chat.state import (
            ChatState,
            ChatInput,
            IntentProfile,
        )

        node = ResponseNode()

        chat_input = ChatInput(
            message="Third message",
            session_id="550e8400-e29b-41d4-a716-446655440000",
        )
        state = ChatState(
            input=chat_input,
            messages=[
                {"role": "user", "content": "First message"},
                {"role": "assistant", "content": "First reply"},
                {"role": "user", "content": "Second message"},
                {"role": "assistant", "content": "Second reply"},
                {"role": "user", "content": "Third message"},
                {"role": "assistant", "content": "Latest reply here"},
            ],
            intent_profile=IntentProfile(),
        )

        result = node(state)

        output = result["output"]
        assert output.response == "Latest reply here"

    def test_node_copies_intent_profile_to_output(self):
        """Node should include current intent profile in output."""
        from agent_will_smith.agent.intent_chat.node.response_node import (
            ResponseNode,
        )
        from agent_will_smith.agent.intent_chat.state import (
            ChatState,
            ChatInput,
            IntentProfile,
        )

        node = ResponseNode()

        chat_input = ChatInput(
            message="Test",
            session_id="550e8400-e29b-41d4-a716-446655440000",
        )
        intent_profile = IntentProfile(
            life_stage="mid_career",
            risk_preference="moderate",
            product_interests=["retirement", "investment"],
            intent_score=0.8,
        )
        state = ChatState(
            input=chat_input,
            messages=[
                {"role": "user", "content": "Test"},
                {"role": "assistant", "content": "Response"},
            ],
            intent_profile=intent_profile,
        )

        result = node(state)

        output = result["output"]
        assert output.intent_profile.life_stage == "mid_career"
        assert output.intent_profile.risk_preference == "moderate"
        assert output.intent_profile.intent_score == 0.8


class TestGetUpdatedIntentProfile:
    """Tests for _get_updated_intent_profile method."""

    def test_applies_financial_goal_from_namespace(self):
        """Test that financial_goal is applied from namespace."""
        from agent_will_smith.agent.intent_chat.node.response_node import (
            ResponseNode,
        )
        from agent_will_smith.agent.intent_chat.state import (
            ChatState,
            ChatInput,
        )
        from agent_will_smith.agent.intent_chat.model.namespaces import (
            ToolExecutionNodeNamespace,
        )

        node = ResponseNode()

        input_data = ChatInput(
            message="test",
            session_id="550e8400-e29b-41d4-a716-446655440000",
        )
        state = ChatState(input=input_data)

        state.tool_execution_node = ToolExecutionNodeNamespace(
            tool_results=[],
            updated_intent_score=0.9,
            updated_product_interests=["retirement"],
            updated_financial_goal={
                "target_age": 50,
                "target_amount": "2000萬",
                "timeline": "5年",
                "goal_type": "retirement",
            },
        )

        updated = node._get_updated_intent_profile(state)

        assert updated.financial_goal is not None
        assert updated.financial_goal.target_age == 50
        assert updated.financial_goal.target_amount == "2000萬"

    def test_applies_all_new_fields_from_namespace(self):
        """Test that all new fields are applied from namespace."""
        from agent_will_smith.agent.intent_chat.node.response_node import (
            ResponseNode,
        )
        from agent_will_smith.agent.intent_chat.state import (
            ChatState,
            ChatInput,
        )
        from agent_will_smith.agent.intent_chat.model.namespaces import (
            ToolExecutionNodeNamespace,
        )

        node = ResponseNode()

        input_data = ChatInput(
            message="test",
            session_id="550e8400-e29b-41d4-a716-446655440000",
        )
        state = ChatState(input=input_data)

        state.tool_execution_node = ToolExecutionNodeNamespace(
            tool_results=[],
            updated_intent_score=0.85,
            updated_product_interests=["investment"],
            updated_life_stage="pre_retirement",
            updated_risk_preference="aggressive",
            updated_investment_experience="intermediate",
            updated_current_assets="1000萬台幣",
        )

        updated = node._get_updated_intent_profile(state)

        assert updated.life_stage == "pre_retirement"
        assert updated.risk_preference == "aggressive"
        assert updated.investment_experience == "intermediate"
        assert updated.current_assets == "1000萬台幣"
