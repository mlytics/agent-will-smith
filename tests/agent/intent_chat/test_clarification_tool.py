"""Tests for clarification tool.

This tool provides clarifying questions/options to gather user intent.
"""

import pytest


class TestClarificationTool:
    """Tests for clarification tool that returns UI options."""

    def test_tool_has_correct_name(self):
        """Tool should be named 'clarification'."""
        from agent_will_smith.agent.intent_chat.tools.clarification_tool import (
            clarification_tool,
        )

        assert clarification_tool.name == "clarification"

    def test_tool_has_description(self):
        """Tool should have a description for the LLM."""
        from agent_will_smith.agent.intent_chat.tools.clarification_tool import (
            clarification_tool,
        )

        assert clarification_tool.description
        assert len(clarification_tool.description) > 10

    def test_tool_has_required_args_schema(self):
        """Tool should define args schema with question and options."""
        from agent_will_smith.agent.intent_chat.tools.clarification_tool import (
            ClarificationToolInput,
        )

        schema = ClarificationToolInput.model_json_schema()
        properties = schema.get("properties", {})

        assert "question" in properties
        assert "options" in properties

    def test_get_clarification_returns_structured_response(self):
        """Tool should return question and options for UI display."""
        from agent_will_smith.agent.intent_chat.tools.clarification_tool import (
            get_clarification,
        )

        result = get_clarification(
            question="What type of investment are you interested in?",
            options=["Stocks", "Bonds", "Mutual Funds", "ETFs"],
            category="investment_type",
        )

        assert result["question"] == "What type of investment are you interested in?"
        assert result["options"] == ["Stocks", "Bonds", "Mutual Funds", "ETFs"]
        assert result["category"] == "investment_type"
        assert result["type"] == "clarification"

    def test_get_clarification_validates_options_not_empty(self):
        """Tool should require at least one option."""
        from agent_will_smith.agent.intent_chat.tools.clarification_tool import (
            get_clarification,
        )

        with pytest.raises(ValueError, match="at least one option"):
            get_clarification(
                question="What do you prefer?",
                options=[],  # Empty options should fail
            )

    def test_get_clarification_validates_question_not_empty(self):
        """Tool should require a non-empty question."""
        from agent_will_smith.agent.intent_chat.tools.clarification_tool import (
            get_clarification,
        )

        with pytest.raises(ValueError, match="question.*empty"):
            get_clarification(
                question="",  # Empty question should fail
                options=["Option A", "Option B"],
            )
