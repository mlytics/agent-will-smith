"""Tests for product recommendation tool.

This tool wraps the existing product_recommendation agent for use in intent_chat.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch


class TestProductRecommendationTool:
    """Tests for product recommendation tool that wraps the existing agent."""

    def test_tool_has_correct_name(self):
        """Tool should be named 'product_recommendation'."""
        from agent_will_smith.agent.intent_chat.tools.product_recommendation_tool import (
            product_recommendation_tool,
        )

        assert product_recommendation_tool.name == "product_recommendation"

    def test_tool_has_description(self):
        """Tool should have a description for the LLM."""
        from agent_will_smith.agent.intent_chat.tools.product_recommendation_tool import (
            product_recommendation_tool,
        )

        assert product_recommendation_tool.description
        assert len(product_recommendation_tool.description) > 10

    def test_tool_has_required_args_schema(self):
        """Tool should define args schema with article, question, k, verticals."""
        from agent_will_smith.agent.intent_chat.tools.product_recommendation_tool import (
            ProductRecommendationToolInput,
        )

        schema = ProductRecommendationToolInput.model_json_schema()
        properties = schema.get("properties", {})

        assert "article" in properties
        assert "question" in properties
        assert "k" in properties
        assert "verticals" in properties

    @pytest.mark.asyncio
    async def test_tool_returns_recommendation_results(self):
        """Tool should return product recommendations from the agent."""
        from agent_will_smith.agent.intent_chat.tools.product_recommendation_tool import (
            get_product_recommendations,
        )

        # Mock the agent container and agent
        mock_output = MagicMock()
        mock_output.model_dump.return_value = {
            "grouped_results": {"activities": [{"product_id": "act-1", "title": "Hiking"}]},
            "total_products": 1,
            "status": "complete",
            "errors": {},
            "intent": "User wants outdoor activities",
        }

        mock_agent = AsyncMock()
        mock_agent.invoke.return_value = mock_output

        mock_container = MagicMock()
        mock_container.agent.return_value = mock_agent

        with patch(
            "agent_will_smith.agent.intent_chat.tools.product_recommendation_tool.get_product_recommendation_agent",
            return_value=mock_agent,
        ):
            result = await get_product_recommendations(
                article="This article is about hiking and outdoor activities...",
                question="What activities can I do?",
                k=5,
                verticals=["activities"],
                customer_uuid="550e8400-e29b-41d4-a716-446655440000",
            )

        assert "grouped_results" in result
        assert result["total_products"] == 1
        assert result["status"] == "complete"

    @pytest.mark.asyncio
    async def test_tool_handles_agent_errors_gracefully(self):
        """Tool should catch agent exceptions and return error dict."""
        from agent_will_smith.agent.intent_chat.tools.product_recommendation_tool import (
            get_product_recommendations,
        )
        from agent_will_smith.core.exceptions import UpstreamError

        mock_agent = AsyncMock()
        mock_agent.invoke.side_effect = UpstreamError("LLM service failed")

        with patch(
            "agent_will_smith.agent.intent_chat.tools.product_recommendation_tool.get_product_recommendation_agent",
            return_value=mock_agent,
        ):
            result = await get_product_recommendations(
                article="Test article content here...",
                question="Test question?",
                k=5,
                verticals=["activities"],
            )

        assert "error" in result
        assert "LLM service failed" in result["error"]
