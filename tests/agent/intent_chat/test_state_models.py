"""Tests for IntentProfile and FinancialGoal models."""

import pytest
from agent_will_smith.agent.intent_chat.state import IntentProfile, FinancialGoal


class TestFinancialGoal:
    """Tests for FinancialGoal model."""

    def test_financial_goal_all_fields(self):
        """Test creating FinancialGoal with all fields."""
        goal = FinancialGoal(
            target_age=50,
            target_amount="2000萬",
            timeline="5年",
            goal_type="retirement",
        )
        assert goal.target_age == 50
        assert goal.target_amount == "2000萬"
        assert goal.timeline == "5年"
        assert goal.goal_type == "retirement"

    def test_financial_goal_optional_fields(self):
        """Test creating FinancialGoal with no fields."""
        goal = FinancialGoal()
        assert goal.target_age is None
        assert goal.target_amount is None
        assert goal.timeline is None
        assert goal.goal_type is None

    def test_financial_goal_partial_fields(self):
        """Test creating FinancialGoal with some fields."""
        goal = FinancialGoal(target_age=55, goal_type="wealth_growth")
        assert goal.target_age == 55
        assert goal.target_amount is None
        assert goal.goal_type == "wealth_growth"
