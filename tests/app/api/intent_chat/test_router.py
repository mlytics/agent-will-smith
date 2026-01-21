"""Tests for intent chat router.

These tests verify the FastAPI endpoints.
"""

import pytest
from unittest.mock import MagicMock, AsyncMock, patch


class TestChatSyncEndpoint:
    """Tests for POST /chat/sync synchronous endpoint."""

    @pytest.mark.asyncio
    async def test_endpoint_exists(self):
        """Router should have a chat sync endpoint."""
        from agent_will_smith.app.api.intent_chat.router import router

        routes = [route.path for route in router.routes]
        assert "/chat/sync" in routes

    @pytest.mark.asyncio
    async def test_endpoint_invokes_agent(self):
        """Endpoint should invoke the agent with ChatInput."""
        from agent_will_smith.app.api.intent_chat.router import chat_sync_endpoint
        from agent_will_smith.app.api.intent_chat.dto import ChatRequest
        from agent_will_smith.agent.intent_chat.state import ChatOutput, IntentProfile

        # Create mock agent
        mock_agent = AsyncMock()
        mock_agent.invoke.return_value = ChatOutput(
            response="Hello! How can I help?",
            intent_profile=IntentProfile(),
            tool_calls=[],
            session_id="550e8400-e29b-41d4-a716-446655440000",
            is_complete=True,
        )

        # Create mock request
        mock_request = MagicMock()
        mock_request.state.trace_id = "trace-123"

        request_body = ChatRequest(
            message="Hello",
            session_id="550e8400-e29b-41d4-a716-446655440000",
        )

        response = await chat_sync_endpoint(
            request=mock_request,
            body=request_body,
            agent=mock_agent,
        )

        mock_agent.invoke.assert_called_once()
        assert response.response == "Hello! How can I help?"
        assert response.session_id == "550e8400-e29b-41d4-a716-446655440000"

    @pytest.mark.asyncio
    async def test_endpoint_transforms_agent_output_to_response(self):
        """Endpoint should transform AgentOutput to ChatResponse."""
        from agent_will_smith.app.api.intent_chat.router import chat_sync_endpoint
        from agent_will_smith.app.api.intent_chat.dto import ChatRequest, ChatResponse
        from agent_will_smith.agent.intent_chat.state import ChatOutput, IntentProfile

        mock_agent = AsyncMock()
        mock_agent.invoke.return_value = ChatOutput(
            response="Let me help with retirement planning.",
            intent_profile=IntentProfile(
                life_stage="mid_career",
                risk_preference="moderate",
                product_interests=["retirement"],
                intent_score=0.75,
            ),
            tool_calls=[{"tool_call_id": "call_1", "result": {"type": "clarification"}}],
            session_id="550e8400-e29b-41d4-a716-446655440000",
            is_complete=True,
        )

        mock_request = MagicMock()
        mock_request.state.trace_id = "trace-123"

        request_body = ChatRequest(
            message="I'm thinking about retirement",
            session_id="550e8400-e29b-41d4-a716-446655440000",
        )

        response = await chat_sync_endpoint(
            request=mock_request,
            body=request_body,
            agent=mock_agent,
        )

        assert isinstance(response, ChatResponse)
        assert response.intent_profile.life_stage == "mid_career"
        assert response.intent_profile.risk_preference == "moderate"
        assert response.intent_profile.intent_score == 0.75
        assert len(response.tool_calls) == 1


class TestQuickQuestionsEndpoint:
    """Tests for GET /quick-questions endpoint."""

    def test_endpoint_exists(self):
        """Router should have a quick-questions endpoint."""
        from agent_will_smith.app.api.intent_chat.router import router

        routes = [route.path for route in router.routes]
        assert "/quick-questions" in routes

    def test_endpoint_returns_questions(self):
        """Endpoint should return a list of quick questions."""
        from agent_will_smith.app.api.intent_chat.router import quick_questions_endpoint
        from agent_will_smith.app.api.intent_chat.dto import QuickQuestionsResponse

        response = quick_questions_endpoint()

        assert isinstance(response, QuickQuestionsResponse)
        assert len(response.questions) > 0


class TestChatStreamingEndpoint:
    """Tests for POST /chat SSE streaming endpoint."""

    @pytest.mark.asyncio
    async def test_endpoint_exists(self):
        """Router should have a chat streaming endpoint."""
        from agent_will_smith.app.api.intent_chat.router import router

        routes = [route.path for route in router.routes]
        assert "/chat" in routes
