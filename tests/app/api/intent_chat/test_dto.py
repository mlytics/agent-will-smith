"""Tests for intent chat API DTOs.

These DTOs define the API request/response schemas.
"""

import pytest
from pydantic import ValidationError


class TestChatRequest:
    """Tests for ChatRequest API schema."""

    def test_chat_request_creates_with_required_fields(self):
        """ChatRequest should create with message and session_id."""
        from agent_will_smith.app.api.intent_chat.dto import ChatRequest

        request = ChatRequest(
            message="Hello, can you help me with retirement planning?",
            session_id="550e8400-e29b-41d4-a716-446655440000",
        )

        assert request.message == "Hello, can you help me with retirement planning?"
        assert request.session_id == "550e8400-e29b-41d4-a716-446655440000"

    def test_chat_request_accepts_optional_context(self):
        """ChatRequest should accept optional context dict."""
        from agent_will_smith.app.api.intent_chat.dto import ChatRequest

        request = ChatRequest(
            message="Test",
            session_id="550e8400-e29b-41d4-a716-446655440000",
            context={"user_age": 35, "region": "US"},
        )

        assert request.context == {"user_age": 35, "region": "US"}

    def test_chat_request_accepts_conversation_history(self):
        """ChatRequest should accept conversation history."""
        from agent_will_smith.app.api.intent_chat.dto import ChatRequest

        request = ChatRequest(
            message="What about bonds?",
            session_id="550e8400-e29b-41d4-a716-446655440000",
            conversation_history=[
                {"role": "user", "content": "I'm interested in investing"},
                {"role": "assistant", "content": "What type of investments?"},
            ],
        )

        assert len(request.conversation_history) == 2

    def test_chat_request_validates_message_not_empty(self):
        """ChatRequest should reject empty messages."""
        from agent_will_smith.app.api.intent_chat.dto import ChatRequest

        with pytest.raises(ValidationError) as exc_info:
            ChatRequest(
                message="",
                session_id="550e8400-e29b-41d4-a716-446655440000",
            )

        assert "message" in str(exc_info.value).lower()

    def test_chat_request_validates_session_id_uuid_format(self):
        """ChatRequest should require valid UUID format for session_id."""
        from agent_will_smith.app.api.intent_chat.dto import ChatRequest

        with pytest.raises(ValidationError) as exc_info:
            ChatRequest(
                message="Hello",
                session_id="not-a-uuid",
            )

        assert "session_id" in str(exc_info.value).lower()


class TestChatResponse:
    """Tests for ChatResponse API schema."""

    def test_chat_response_creates_with_required_fields(self):
        """ChatResponse should create with all required fields."""
        from agent_will_smith.app.api.intent_chat.dto import (
            ChatResponse,
            IntentProfileResponse,
        )

        response = ChatResponse(
            response="Hello! I'd be happy to help with retirement planning.",
            intent_profile=IntentProfileResponse(),
            tool_calls=[],
            session_id="550e8400-e29b-41d4-a716-446655440000",
            is_complete=True,
        )

        assert response.response == "Hello! I'd be happy to help with retirement planning."
        assert response.session_id == "550e8400-e29b-41d4-a716-446655440000"
        assert response.is_complete is True

    def test_chat_response_includes_tool_calls(self):
        """ChatResponse should include tool call results."""
        from agent_will_smith.app.api.intent_chat.dto import (
            ChatResponse,
            IntentProfileResponse,
        )

        response = ChatResponse(
            response="Let me clarify your risk preference.",
            intent_profile=IntentProfileResponse(),
            tool_calls=[
                {"tool_call_id": "call_123", "result": {"question": "What is your risk level?"}}
            ],
            session_id="550e8400-e29b-41d4-a716-446655440000",
            is_complete=True,
        )

        assert len(response.tool_calls) == 1
        assert response.tool_calls[0]["tool_call_id"] == "call_123"


class TestIntentProfileResponse:
    """Tests for IntentProfileResponse API schema."""

    def test_intent_profile_response_has_all_fields(self):
        """IntentProfileResponse should expose all intent fields."""
        from agent_will_smith.app.api.intent_chat.dto import IntentProfileResponse

        profile = IntentProfileResponse(
            life_stage="mid_career",
            risk_preference="moderate",
            product_interests=["retirement", "investment"],
            intent_score=0.85,
        )

        assert profile.life_stage == "mid_career"
        assert profile.risk_preference == "moderate"
        assert profile.product_interests == ["retirement", "investment"]
        assert profile.intent_score == 0.85

    def test_intent_profile_response_has_defaults(self):
        """IntentProfileResponse should have sensible defaults."""
        from agent_will_smith.app.api.intent_chat.dto import IntentProfileResponse

        profile = IntentProfileResponse()

        assert profile.life_stage is None
        assert profile.risk_preference is None
        assert profile.product_interests == []
        assert profile.intent_score == 0.0


class TestQuickQuestionsResponse:
    """Tests for QuickQuestionsResponse API schema."""

    def test_quick_questions_response_contains_questions(self):
        """QuickQuestionsResponse should contain a list of quick questions."""
        from agent_will_smith.app.api.intent_chat.dto import (
            QuickQuestionsResponse,
            QuickQuestion,
        )

        response = QuickQuestionsResponse(
            questions=[
                QuickQuestion(id="q1", text="What are your retirement goals?", category="retirement"),
                QuickQuestion(id="q2", text="What is your risk tolerance?", category="risk"),
            ]
        )

        assert len(response.questions) == 2
        assert response.questions[0].id == "q1"
        assert response.questions[0].category == "retirement"
