"""Tests for intent capture tool.

This tool records intent signals detected from user conversation.
"""

import pytest
from datetime import datetime, timezone


class TestIntentCaptureTool:
    """Tests for intent capture tool that records intent signals."""

    def test_tool_has_correct_name(self):
        """Tool should be named 'intent_capture'."""
        from agent_will_smith.agent.intent_chat.tools.intent_capture_tool import (
            intent_capture_tool,
        )

        assert intent_capture_tool.name == "intent_capture"

    def test_tool_has_description(self):
        """Tool should have a description for the LLM."""
        from agent_will_smith.agent.intent_chat.tools.intent_capture_tool import (
            intent_capture_tool,
        )

        assert intent_capture_tool.description
        assert len(intent_capture_tool.description) > 10

    def test_tool_has_required_args_schema(self):
        """Tool should define args schema with category, signal_type, confidence."""
        from agent_will_smith.agent.intent_chat.tools.intent_capture_tool import (
            IntentCaptureToolInput,
        )

        schema = IntentCaptureToolInput.model_json_schema()
        properties = schema.get("properties", {})

        assert "category" in properties
        assert "signal_type" in properties
        assert "confidence" in properties

    def test_capture_intent_creates_valid_signal(self):
        """Tool should create a valid IntentSignal from input."""
        from agent_will_smith.agent.intent_chat.tools.intent_capture_tool import (
            capture_intent,
        )

        result = capture_intent(
            category="retirement",
            signal_type="explicit",
            confidence=0.9,
        )

        assert result["category"] == "retirement"
        assert result["signal_type"] == "explicit"
        assert result["confidence"] == 0.9
        assert result["type"] == "intent_signal"
        assert "timestamp" in result

    def test_capture_intent_validates_confidence_range(self):
        """Tool should validate confidence is between 0.0 and 1.0."""
        from agent_will_smith.agent.intent_chat.tools.intent_capture_tool import (
            capture_intent,
        )

        # Confidence > 1.0 should fail
        with pytest.raises(ValueError, match="confidence"):
            capture_intent(
                category="investment",
                signal_type="inferred",
                confidence=1.5,
            )

        # Confidence < 0.0 should fail
        with pytest.raises(ValueError, match="confidence"):
            capture_intent(
                category="investment",
                signal_type="inferred",
                confidence=-0.1,
            )

    def test_capture_intent_validates_signal_type(self):
        """Tool should validate signal_type is explicit, inferred, or clarified."""
        from agent_will_smith.agent.intent_chat.tools.intent_capture_tool import (
            capture_intent,
        )

        with pytest.raises(ValueError, match="signal_type"):
            capture_intent(
                category="investment",
                signal_type="invalid_type",
                confidence=0.8,
            )

    def test_capture_intent_accepts_all_valid_signal_types(self):
        """Tool should accept all valid signal types."""
        from agent_will_smith.agent.intent_chat.tools.intent_capture_tool import (
            capture_intent,
        )

        for signal_type in ["explicit", "inferred", "clarified"]:
            result = capture_intent(
                category="test",
                signal_type=signal_type,
                confidence=0.7,
            )
            assert result["signal_type"] == signal_type
