"""Tests for intent chat agent state schemas."""

from datetime import datetime
import pytest
from pydantic import ValidationError


class TestIntentSignal:
    """Tests for IntentSignal model."""

    def test_intent_signal_creates_with_valid_data(self):
        """IntentSignal should create with valid signal_type, category, confidence."""
        from agent_will_smith.agent.intent_chat.state import IntentSignal

        signal = IntentSignal(
            signal_type="explicit",
            category="retirement",
            confidence=0.85,
        )

        assert signal.signal_type == "explicit"
        assert signal.category == "retirement"
        assert signal.confidence == 0.85
        assert isinstance(signal.timestamp, datetime)

    def test_intent_signal_validates_signal_type_literal(self):
        """IntentSignal should only accept explicit, inferred, or clarified."""
        from agent_will_smith.agent.intent_chat.state import IntentSignal

        with pytest.raises(ValidationError):
            IntentSignal(
                signal_type="invalid_type",
                category="retirement",
                confidence=0.85,
            )

    def test_intent_signal_validates_confidence_range(self):
        """IntentSignal confidence must be between 0.0 and 1.0."""
        from agent_will_smith.agent.intent_chat.state import IntentSignal

        with pytest.raises(ValidationError):
            IntentSignal(
                signal_type="explicit",
                category="retirement",
                confidence=1.5,  # Invalid
            )


class TestIntentProfile:
    """Tests for IntentProfile model."""

    def test_intent_profile_creates_with_defaults(self):
        """IntentProfile should have sensible defaults."""
        from agent_will_smith.agent.intent_chat.state import IntentProfile

        profile = IntentProfile()

        assert profile.life_stage is None
        assert profile.risk_preference is None
        assert profile.product_interests == []
        assert profile.intent_score == 0.0
        assert profile.signals == []

    def test_intent_profile_validates_risk_preference_literal(self):
        """IntentProfile risk_preference must be conservative, moderate, or aggressive."""
        from agent_will_smith.agent.intent_chat.state import IntentProfile

        with pytest.raises(ValidationError):
            IntentProfile(risk_preference="very_risky")

    def test_intent_profile_validates_intent_score_range(self):
        """IntentProfile intent_score must be between 0.0 and 1.0."""
        from agent_will_smith.agent.intent_chat.state import IntentProfile

        with pytest.raises(ValidationError):
            IntentProfile(intent_score=1.5)

    def test_intent_profile_accepts_valid_risk_preferences(self):
        """IntentProfile should accept all valid risk preference values."""
        from agent_will_smith.agent.intent_chat.state import IntentProfile

        for preference in ["conservative", "moderate", "aggressive"]:
            profile = IntentProfile(risk_preference=preference)
            assert profile.risk_preference == preference


class TestChatInput:
    """Tests for ChatInput model."""

    def test_chat_input_creates_with_required_fields(self):
        """ChatInput should create with message and session_id."""
        from agent_will_smith.agent.intent_chat.state import ChatInput

        chat_input = ChatInput(
            message="I'm looking for retirement advice",
            session_id="550e8400-e29b-41d4-a716-446655440000",
        )

        assert chat_input.message == "I'm looking for retirement advice"
        assert chat_input.session_id == "550e8400-e29b-41d4-a716-446655440000"
        assert chat_input.context is None
        assert chat_input.conversation_history == []

    def test_chat_input_validates_message_length(self):
        """ChatInput message must be between 1 and 5000 characters."""
        from agent_will_smith.agent.intent_chat.state import ChatInput

        # Empty message should fail
        with pytest.raises(ValidationError):
            ChatInput(
                message="",
                session_id="550e8400-e29b-41d4-a716-446655440000",
            )

        # Too long message should fail
        with pytest.raises(ValidationError):
            ChatInput(
                message="x" * 5001,
                session_id="550e8400-e29b-41d4-a716-446655440000",
            )

    def test_chat_input_validates_session_id_uuid_format(self):
        """ChatInput session_id must be a valid UUID format."""
        from agent_will_smith.agent.intent_chat.state import ChatInput

        with pytest.raises(ValidationError):
            ChatInput(
                message="Hello",
                session_id="not-a-uuid",
            )

    def test_chat_input_accepts_optional_context(self):
        """ChatInput should accept optional context dict."""
        from agent_will_smith.agent.intent_chat.state import ChatInput

        chat_input = ChatInput(
            message="Hello",
            session_id="550e8400-e29b-41d4-a716-446655440000",
            context={"article_id": "art-123", "page": "home"},
        )

        assert chat_input.context == {"article_id": "art-123", "page": "home"}


class TestChatOutput:
    """Tests for ChatOutput model."""

    def test_chat_output_creates_with_required_fields(self):
        """ChatOutput should create with response, intent_profile, session_id."""
        from agent_will_smith.agent.intent_chat.state import ChatOutput, IntentProfile

        output = ChatOutput(
            response="Here's my recommendation...",
            intent_profile=IntentProfile(),
            session_id="550e8400-e29b-41d4-a716-446655440000",
        )

        assert output.response == "Here's my recommendation..."
        assert isinstance(output.intent_profile, IntentProfile)
        assert output.tool_calls == []
        assert output.is_complete is True

    def test_chat_output_validates_response_not_empty(self):
        """ChatOutput response must not be empty."""
        from agent_will_smith.agent.intent_chat.state import ChatOutput, IntentProfile

        with pytest.raises(ValidationError):
            ChatOutput(
                response="",
                intent_profile=IntentProfile(),
                session_id="550e8400-e29b-41d4-a716-446655440000",
            )


class TestChatState:
    """Tests for ChatState model."""

    def test_chat_state_creates_with_input(self):
        """ChatState should create with just input, all other fields optional."""
        from agent_will_smith.agent.intent_chat.state import ChatState, ChatInput

        chat_input = ChatInput(
            message="Hello",
            session_id="550e8400-e29b-41d4-a716-446655440000",
        )
        state = ChatState(input=chat_input)

        assert state.input == chat_input
        assert state.output is None
        assert state.messages == []
        assert state.intent_profile.intent_score == 0.0
        assert state.current_tool_calls == []
        assert state.conversation_node is None
        assert state.tool_calling_node is None
        assert state.tool_execution_node is None
        assert state.response_node is None

    def test_chat_state_has_all_required_namespace_fields(self):
        """ChatState should have fields for all node namespaces."""
        from agent_will_smith.agent.intent_chat.state import ChatState, ChatInput
        from agent_will_smith.agent.intent_chat.model.namespaces import (
            ConversationNodeNamespace,
            ToolCallingNodeNamespace,
            ToolExecutionNodeNamespace,
            ResponseNodeNamespace,
        )

        chat_input = ChatInput(
            message="Hello",
            session_id="550e8400-e29b-41d4-a716-446655440000",
        )
        state = ChatState(
            input=chat_input,
            conversation_node=ConversationNodeNamespace(messages_added=1, tokens_used=100),
            tool_calling_node=ToolCallingNodeNamespace(),
            tool_execution_node=ToolExecutionNodeNamespace(),
            response_node=ResponseNodeNamespace(response_text="Hi!"),
        )

        assert state.conversation_node.messages_added == 1
        assert state.conversation_node.tokens_used == 100
        assert state.response_node.response_text == "Hi!"
