"""Tests for conversation logger."""

import tempfile
from pathlib import Path
from typing import Generator

import pytest

from agent_will_smith.conversation_analytics.database import ConversationDatabase
from agent_will_smith.conversation_analytics.logger import ConversationLogger


class TestConversationLogger:
    """Tests for ConversationLogger."""

    @pytest.fixture
    def logger(self) -> Generator[ConversationLogger, None, None]:
        """Create a logger with temporary database."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"
            db = ConversationDatabase(db_path)
            yield ConversationLogger(db)

    @pytest.mark.asyncio
    async def test_ensure_session_creates_new(
        self, logger: ConversationLogger
    ) -> None:
        """Test that ensure_session creates a new session."""
        await logger.ensure_session("new-session", "cxo_wealth")

        session = logger.db.get_session("new-session")
        assert session is not None
        assert session.scenario_id == "cxo_wealth"

    @pytest.mark.asyncio
    async def test_ensure_session_idempotent(
        self, logger: ConversationLogger
    ) -> None:
        """Test that ensure_session is idempotent."""
        await logger.ensure_session("same-session", "young_starter")
        await logger.ensure_session("same-session", "different_scenario")

        session = logger.db.get_session("same-session")
        assert session is not None
        # Should keep original scenario_id
        assert session.scenario_id == "young_starter"

    @pytest.mark.asyncio
    async def test_log_turn(self, logger: ConversationLogger) -> None:
        """Test logging a conversation turn."""
        await logger.ensure_session("log-test", "free_form")

        await logger.log_turn(
            session_id="log-test",
            user_message="What is retirement planning?",
            assistant_response="Retirement planning involves...",
            response_time_ms=1500,
            tool_calls=[{"tool": "intent_capture", "args": {"category": "retirement"}}],
            intent_profile={"intent_score": 0.6, "product_interests": ["retirement"]},
        )

        turns = logger.db.get_turns("log-test")
        assert len(turns) == 1
        assert turns[0].turn_number == 1
        assert turns[0].user_message == "What is retirement planning?"

        session = logger.db.get_session("log-test")
        assert session is not None
        assert session.turn_count == 1
        assert session.final_intent_profile["intent_score"] == 0.6

    @pytest.mark.asyncio
    async def test_log_multiple_turns(self, logger: ConversationLogger) -> None:
        """Test logging multiple turns increments turn_number."""
        await logger.ensure_session("multi-turn", "retiree_stable")

        for i in range(3):
            await logger.log_turn(
                session_id="multi-turn",
                user_message=f"Message {i+1}",
                assistant_response=f"Response {i+1}",
                response_time_ms=100,
                tool_calls=[],
                intent_profile={"intent_score": 0.1 * (i + 1)},
            )

        turns = logger.db.get_turns("multi-turn")
        assert len(turns) == 3
        assert [t.turn_number for t in turns] == [1, 2, 3]

        session = logger.db.get_session("multi-turn")
        assert session is not None
        assert session.turn_count == 3

    @pytest.mark.asyncio
    async def test_end_session(self, logger: ConversationLogger) -> None:
        """Test ending a session sets ended_at timestamp."""
        await logger.ensure_session("end-test", "cxo_wealth")

        session_before = logger.db.get_session("end-test")
        assert session_before is not None
        assert session_before.ended_at is None

        await logger.end_session("end-test")

        session_after = logger.db.get_session("end-test")
        assert session_after is not None
        assert session_after.ended_at is not None

    @pytest.mark.asyncio
    async def test_turn_count_persistence_across_sessions(
        self, logger: ConversationLogger
    ) -> None:
        """Test that turn counts are correctly restored from existing sessions."""
        # Create session and add turns
        await logger.ensure_session("persist-test", "young_starter")
        await logger.log_turn(
            session_id="persist-test",
            user_message="First message",
            assistant_response="First response",
            response_time_ms=100,
            tool_calls=[],
            intent_profile={},
        )
        await logger.log_turn(
            session_id="persist-test",
            user_message="Second message",
            assistant_response="Second response",
            response_time_ms=100,
            tool_calls=[],
            intent_profile={},
        )

        # Simulate a new logger instance reconnecting to the same session
        # by calling ensure_session again (which should restore turn count)
        new_logger = ConversationLogger(logger.db)
        await new_logger.ensure_session("persist-test", "young_starter")

        # The next turn should be turn 3, not turn 1
        await new_logger.log_turn(
            session_id="persist-test",
            user_message="Third message",
            assistant_response="Third response",
            response_time_ms=100,
            tool_calls=[],
            intent_profile={},
        )

        turns = logger.db.get_turns("persist-test")
        assert len(turns) == 3
        assert turns[2].turn_number == 3
