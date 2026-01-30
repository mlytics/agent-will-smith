"""Unit tests for LangGraph node namespace models.

Tests intent validation constraints (min/max length).
Focus: LLM output validation boundaries.
"""

import pytest
from pydantic import ValidationError

from agent_will_smith.agent.product_recommendation.model.namespaces import (
    IntentNodeNamespace,
)


class TestIntentNodeNamespace:
    """Tests for IntentNodeNamespace intent validation."""

    def test_valid_intent_within_bounds(self):
        """Intent within min/max length should pass."""
        intent = IntentNodeNamespace(
            intent="The user is interested in sustainable living practices."
        )
        assert len(intent.intent) >= 10
        assert len(intent.intent) <= 1000

    def test_intent_exactly_at_minimum_length(self):
        """Intent with exactly 10 characters should pass (boundary: at min)."""
        intent = IntentNodeNamespace(intent="1234567890")  # exactly 10 chars
        assert len(intent.intent) == 10

    def test_intent_below_minimum_length_raises_error(self):
        """Intent with 9 characters should raise ValidationError (boundary: under min)."""
        with pytest.raises(ValidationError) as exc_info:
            IntentNodeNamespace(intent="123456789")  # 9 chars
        assert "intent" in str(exc_info.value).lower()

    def test_intent_exactly_at_maximum_length(self):
        """Intent with exactly 1000 characters should pass (boundary: at max)."""
        intent = IntentNodeNamespace(intent="a" * 1000)
        assert len(intent.intent) == 1000

    def test_intent_above_maximum_length_raises_error(self):
        """Intent with 1001 characters should raise ValidationError (boundary: over max)."""
        with pytest.raises(ValidationError) as exc_info:
            IntentNodeNamespace(intent="a" * 1001)
        assert "intent" in str(exc_info.value).lower()

    def test_empty_intent_raises_error(self):
        """Empty intent should raise ValidationError."""
        with pytest.raises(ValidationError):
            IntentNodeNamespace(intent="")
