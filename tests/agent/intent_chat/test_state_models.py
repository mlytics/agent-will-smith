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


class TestIntentProfileExtended:
    """Tests for extended IntentProfile fields."""

    def test_intent_profile_with_financial_goal(self):
        """Test IntentProfile with financial_goal field."""
        goal = FinancialGoal(target_age=50, target_amount="2000萬")
        profile = IntentProfile(
            life_stage="pre_retirement",
            financial_goal=goal,
        )
        assert profile.financial_goal is not None
        assert profile.financial_goal.target_age == 50

    def test_intent_profile_with_new_fields(self):
        """Test IntentProfile with current_assets and investment_experience."""
        profile = IntentProfile(
            current_assets="1000萬台幣",
            investment_experience="intermediate",
        )
        assert profile.current_assets == "1000萬台幣"
        assert profile.investment_experience == "intermediate"

    def test_intent_profile_defaults(self):
        """Test IntentProfile new fields default to None."""
        profile = IntentProfile()
        assert profile.financial_goal is None
        assert profile.current_assets is None
        assert profile.investment_experience is None
