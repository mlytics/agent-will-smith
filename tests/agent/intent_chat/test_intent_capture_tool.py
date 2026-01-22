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

    def test_capture_with_life_stage(self):
        """Test capture with life_stage parameter."""
        from agent_will_smith.agent.intent_chat.tools.intent_capture_tool import (
            capture_intent,
        )

        result = capture_intent(
            category="retirement",
            signal_type="inferred",
            confidence=0.8,
            life_stage="pre_retirement",
        )
        assert result["life_stage"] == "pre_retirement"

    def test_capture_with_risk_preference(self):
        """Test capture with risk_preference parameter."""
        from agent_will_smith.agent.intent_chat.tools.intent_capture_tool import (
            capture_intent,
        )

        result = capture_intent(
            category="investment",
            signal_type="explicit",
            confidence=0.85,
            risk_preference="aggressive",
        )
        assert result["risk_preference"] == "aggressive"

    def test_capture_with_financial_goal(self):
        """Test capture with financial goal parameters."""
        from agent_will_smith.agent.intent_chat.tools.intent_capture_tool import (
            capture_intent,
        )

        result = capture_intent(
            category="retirement",
            signal_type="explicit",
            confidence=0.9,
            target_age=50,
            target_amount="2000萬",
            timeline="5年",
            goal_type="retirement",
        )
        assert result["target_age"] == 50
        assert result["target_amount"] == "2000萬"
        assert result["timeline"] == "5年"
        assert result["goal_type"] == "retirement"

    def test_capture_with_assets_and_experience(self):
        """Test capture with current_assets and investment_experience."""
        from agent_will_smith.agent.intent_chat.tools.intent_capture_tool import (
            capture_intent,
        )

        result = capture_intent(
            category="investment",
            signal_type="explicit",
            confidence=0.8,
            current_assets="1000萬台幣",
            investment_experience="intermediate",
        )
        assert result["current_assets"] == "1000萬台幣"
        assert result["investment_experience"] == "intermediate"

    def test_capture_full_parameters(self):
        """Test capture with all parameters filled."""
        from agent_will_smith.agent.intent_chat.tools.intent_capture_tool import (
            capture_intent,
        )

        result = capture_intent(
            category="retirement",
            signal_type="clarified",
            confidence=0.95,
            life_stage="pre_retirement",
            risk_preference="aggressive",
            investment_experience="experienced",
            target_age=50,
            target_amount="2000萬",
            timeline="5年",
            goal_type="retirement",
            current_assets="1000萬台幣",
        )
        assert result["category"] == "retirement"
        assert result["life_stage"] == "pre_retirement"
        assert result["risk_preference"] == "aggressive"
        assert result["investment_experience"] == "experienced"
        assert result["target_age"] == 50
        assert result["target_amount"] == "2000萬"
        assert result["current_assets"] == "1000萬台幣"

    def test_optional_fields_not_included_when_none(self):
        """Test that optional fields are not included in result when None."""
        from agent_will_smith.agent.intent_chat.tools.intent_capture_tool import (
            capture_intent,
        )

        result = capture_intent(
            category="retirement",
            signal_type="explicit",
            confidence=0.9,
        )
        # Only required fields and type/timestamp should be in result
        assert "life_stage" not in result
        assert "risk_preference" not in result
        assert "investment_experience" not in result
        assert "target_age" not in result
        assert "target_amount" not in result
        assert "timeline" not in result
        assert "goal_type" not in result
        assert "current_assets" not in result

    def test_validate_risk_preference(self):
        """Test that risk_preference validates allowed values."""
        from agent_will_smith.agent.intent_chat.tools.intent_capture_tool import (
            capture_intent,
        )

        # Valid values should work
        for pref in ["conservative", "moderate", "aggressive"]:
            result = capture_intent(
                category="investment",
                signal_type="explicit",
                confidence=0.8,
                risk_preference=pref,
            )
            assert result["risk_preference"] == pref

        # Invalid value should raise
        with pytest.raises(ValueError, match="risk_preference"):
            capture_intent(
                category="investment",
                signal_type="explicit",
                confidence=0.8,
                risk_preference="invalid_preference",
            )

    def test_validate_investment_experience(self):
        """Test that investment_experience validates allowed values."""
        from agent_will_smith.agent.intent_chat.tools.intent_capture_tool import (
            capture_intent,
        )

        # Valid values should work
        for exp in ["beginner", "intermediate", "experienced"]:
            result = capture_intent(
                category="investment",
                signal_type="explicit",
                confidence=0.8,
                investment_experience=exp,
            )
            assert result["investment_experience"] == exp

        # Invalid value should raise
        with pytest.raises(ValueError, match="investment_experience"):
            capture_intent(
                category="investment",
                signal_type="explicit",
                confidence=0.8,
                investment_experience="invalid_experience",
            )
