"""Integration tests for conversation analytics system.

Tests the complete flow of logging conversation turns with scenarios.
"""

import tempfile
from pathlib import Path
from typing import Generator

import pytest

from agent_will_smith.conversation_analytics.database import ConversationDatabase
from agent_will_smith.conversation_analytics.logger import ConversationLogger
from agent_will_smith.conversation_analytics.scenarios import get_scenario, list_scenarios


class TestConversationAnalyticsIntegration:
    """Integration tests for the complete analytics flow."""

    @pytest.fixture
    def logger(self) -> Generator[ConversationLogger, None, None]:
        """Create a logger with temporary database."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"
            db = ConversationDatabase(db_path)
            yield ConversationLogger(db)

    @pytest.mark.asyncio
    async def test_full_flow_with_predefined_scenario(
        self, logger: ConversationLogger
    ) -> None:
        """Test complete flow: select scenario, log turns, verify data."""
        # Get a predefined scenario
        scenario = get_scenario("cxo_wealth")
        assert scenario is not None
        assert "Executive" in scenario.name or "CXO" in scenario.name.upper()

        # Start a session with this scenario
        session_id = "integration-test-001"
        await logger.ensure_session(session_id, scenario.scenario_id)

        # Simulate a conversation
        turns_data = [
            {
                "user": "我是公司的執行長，想了解退休規劃",
                "assistant": "作為企業主，您的退休規劃需要考慮多方面因素...",
                "tool_calls": [{"tool": "intent_capture", "args": {"life_stage": "working"}}],
                "profile": {"intent_score": 0.3, "life_stage": "working"},
            },
            {
                "user": "我比較關心稅務效率",
                "assistant": "稅務規劃是高資產客戶的重要考量...",
                "tool_calls": [{"tool": "intent_capture", "args": {"interests": ["tax"]}}],
                "profile": {"intent_score": 0.6, "life_stage": "working", "interests": ["tax"]},
            },
            {
                "user": "有什麼推薦的產品嗎？",
                "assistant": "基於您的需求，我推薦以下產品...",
                "tool_calls": [{"tool": "product_recommendation"}],
                "profile": {"intent_score": 0.9, "life_stage": "working", "interests": ["tax", "retirement"]},
            },
        ]

        # Log each turn
        for i, turn in enumerate(turns_data):
            await logger.log_turn(
                session_id=session_id,
                user_message=turn["user"],
                assistant_response=turn["assistant"],
                response_time_ms=1000 + i * 500,
                tool_calls=turn["tool_calls"],
                intent_profile=turn["profile"],
            )

        # End the session
        await logger.end_session(session_id)

        # Verify session data
        session = logger.db.get_session(session_id)
        assert session is not None
        assert session.scenario_id == "cxo_wealth"
        assert session.turn_count == 3
        assert session.ended_at is not None
        assert session.final_intent_profile["intent_score"] == 0.9

        # Verify turn data
        turns = logger.db.get_turns(session_id)
        assert len(turns) == 3
        assert turns[0].turn_number == 1
        assert turns[1].turn_number == 2
        assert turns[2].turn_number == 3
        assert "執行長" in turns[0].user_message
        assert turns[2].tool_calls[0]["tool"] == "product_recommendation"

    @pytest.mark.asyncio
    async def test_free_form_scenario(self, logger: ConversationLogger) -> None:
        """Test free-form scenario without predefined expectations."""
        scenario = get_scenario("free_form")
        assert scenario is not None
        assert scenario.expected_intents == []

        session_id = "free-form-test"
        await logger.ensure_session(session_id, scenario.scenario_id)

        await logger.log_turn(
            session_id=session_id,
            user_message="隨便問個問題",
            assistant_response="好的，請問有什麼需要幫助的？",
            response_time_ms=500,
            tool_calls=[],
            intent_profile={},
        )

        session = logger.db.get_session(session_id)
        assert session is not None
        assert session.scenario_id == "free_form"

    @pytest.mark.asyncio
    async def test_multiple_sessions_same_scenario(
        self, logger: ConversationLogger
    ) -> None:
        """Test multiple sessions can use the same scenario."""
        scenario_id = "young_starter"

        for i in range(3):
            session_id = f"multi-session-{i}"
            await logger.ensure_session(session_id, scenario_id)
            await logger.log_turn(
                session_id=session_id,
                user_message=f"Session {i} message",
                assistant_response=f"Session {i} response",
                response_time_ms=100,
                tool_calls=[],
                intent_profile={"session": i},
            )

        # List sessions for this scenario
        sessions = logger.db.list_sessions(scenario_id=scenario_id)
        assert len(sessions) == 3
        for session in sessions:
            assert session.scenario_id == scenario_id

    def test_all_scenarios_are_defined(self) -> None:
        """Verify all expected scenarios are defined."""
        scenarios = list_scenarios()
        scenario_ids = [s.scenario_id for s in scenarios]

        expected_ids = [
            "cxo_wealth",
            "young_starter",
            "retiree_stable",
            "family_education",
            "free_form",
        ]

        for expected_id in expected_ids:
            assert expected_id in scenario_ids, f"Missing scenario: {expected_id}"

    def test_scenarios_have_required_fields(self) -> None:
        """Verify all scenarios have required fields."""
        scenarios = list_scenarios()

        for scenario in scenarios:
            assert scenario.scenario_id, f"Scenario missing scenario_id"
            assert scenario.name, f"Scenario {scenario.scenario_id} missing name"
            assert scenario.icon, f"Scenario {scenario.scenario_id} missing icon"
            assert scenario.short_desc, f"Scenario {scenario.scenario_id} missing short_desc"
