"""Conversation logger for recording test sessions.

Provides a high-level API for logging conversation turns to the database.
"""

from datetime import datetime, timezone
from typing import Any

import structlog

from agent_will_smith.conversation_analytics.database import ConversationDatabase
from agent_will_smith.conversation_analytics.models import ConversationTurn


class ConversationLogger:
    """Logs conversation turns to the database.

    This class wraps the ConversationDatabase and provides a high-level API
    for recording conversation sessions and turns during testing.

    Attributes:
        db: The underlying ConversationDatabase instance.
        logger: Structured logger for this class.
    """

    def __init__(self, database: ConversationDatabase) -> None:
        """Initialize the conversation logger.

        Args:
            database: The ConversationDatabase instance to use for persistence.
        """
        self.db = database
        self.logger = structlog.get_logger(__name__)
        self._turn_counts: dict[str, int] = {}

    async def ensure_session(self, session_id: str, scenario_id: str) -> None:
        """Ensure a session exists, creating if necessary.

        This method is idempotent - calling it multiple times with the same
        session_id will not modify the existing session.

        Args:
            session_id: Unique identifier for the session.
            scenario_id: ID of the scenario being tested.
        """
        existing = self.db.get_session(session_id)
        if not existing:
            self.db.create_session(session_id, scenario_id)
            self._turn_counts[session_id] = 0
            self.logger.info(
                "created_new_session",
                session_id=session_id,
                scenario_id=scenario_id,
            )
        else:
            self._turn_counts[session_id] = existing.turn_count

    async def log_turn(
        self,
        session_id: str,
        user_message: str,
        assistant_response: str,
        response_time_ms: int,
        tool_calls: list[dict[str, Any]],
        intent_profile: dict[str, Any],
    ) -> None:
        """Log a single conversation turn.

        Adds a new turn to the database and updates the session's turn count
        and final intent profile.

        Args:
            session_id: The session ID this turn belongs to.
            user_message: The user's message text.
            assistant_response: The assistant's response text.
            response_time_ms: Response time in milliseconds.
            tool_calls: List of tool calls made during this turn.
            intent_profile: Current intent profile snapshot after this turn.
        """
        turn_number = self._turn_counts.get(session_id, 0) + 1
        self._turn_counts[session_id] = turn_number

        turn = ConversationTurn(
            session_id=session_id,
            turn_number=turn_number,
            timestamp=datetime.now(timezone.utc),
            user_message=user_message,
            assistant_response=assistant_response,
            response_time_ms=response_time_ms,
            tool_calls=tool_calls,
            intent_profile_snapshot=intent_profile,
        )

        self.db.add_turn(turn)
        self.db.update_session(
            session_id,
            turn_count=turn_number,
            final_intent_profile=intent_profile,
        )

        self.logger.info(
            "logged_conversation_turn",
            session_id=session_id,
            turn_number=turn_number,
            response_time_ms=response_time_ms,
            tool_calls_count=len(tool_calls),
        )

    async def end_session(self, session_id: str) -> None:
        """Mark a session as ended.

        Sets the ended_at timestamp on the session to the current time.

        Args:
            session_id: The session ID to end.
        """
        self.db.update_session(session_id, ended_at=datetime.now(timezone.utc))
        self.logger.info("ended_session", session_id=session_id)
