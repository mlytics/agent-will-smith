"""SQLite database for conversation analytics.

Provides persistence for test sessions and conversation turns using SQLite.
"""

import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Generator, Optional

import structlog

from agent_will_smith.conversation_analytics.models import ConversationTurn, TestSession

logger = structlog.get_logger(__name__)


class ConversationDatabase:
    """SQLite database for storing conversation analytics data.

    This class provides methods for creating, reading, and updating
    test sessions and conversation turns.

    Attributes:
        db_path: Path to the SQLite database file.
    """

    def __init__(self, db_path: str | Path = "conversation_analytics.db") -> None:
        """Initialize the database.

        Args:
            db_path: Path to the SQLite database file. Defaults to
                     'conversation_analytics.db' in the current directory.
        """
        self.db_path = Path(db_path)
        self._init_schema()

    def _init_schema(self) -> None:
        """Initialize the database schema if not exists."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS sessions (
                    session_id TEXT PRIMARY KEY,
                    scenario_id TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    ended_at TEXT,
                    final_intent_profile TEXT,
                    turn_count INTEGER DEFAULT 0,
                    inferred_scenario TEXT
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS turns (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    turn_number INTEGER NOT NULL,
                    timestamp TEXT NOT NULL,
                    user_message TEXT NOT NULL,
                    assistant_response TEXT NOT NULL,
                    response_time_ms INTEGER,
                    tool_calls TEXT,
                    intent_profile_snapshot TEXT,
                    FOREIGN KEY (session_id) REFERENCES sessions(session_id)
                )
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_turns_session_id ON turns(session_id)
            """)
            conn.commit()
        logger.debug("database_schema_initialized", db_path=str(self.db_path))

    @contextmanager
    def _get_connection(self) -> Generator[sqlite3.Connection, None, None]:
        """Get a database connection as a context manager.

        Yields:
            SQLite connection object.
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()

    def create_session(self, session_id: str, scenario_id: str) -> TestSession:
        """Create a new test session.

        Args:
            session_id: Unique identifier for the session.
            scenario_id: ID of the scenario being tested.

        Returns:
            The created TestSession.
        """
        created_at = datetime.now(timezone.utc)
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO sessions (session_id, scenario_id, created_at, turn_count)
                VALUES (?, ?, ?, 0)
                """,
                (session_id, scenario_id, created_at.isoformat()),
            )
            conn.commit()

        logger.info(
            "session_created",
            session_id=session_id,
            scenario_id=scenario_id,
        )

        return TestSession(
            session_id=session_id,
            scenario_id=scenario_id,
            created_at=created_at,
            turn_count=0,
        )

    def get_session(self, session_id: str) -> TestSession | None:
        """Get a test session by ID.

        Args:
            session_id: The session ID to look up.

        Returns:
            The TestSession if found, None otherwise.
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM sessions WHERE session_id = ?",
                (session_id,),
            )
            row = cursor.fetchone()

        if row is None:
            return None

        return self._row_to_session(row)

    def update_session(
        self,
        session_id: str,
        turn_count: Optional[int] = None,
        final_intent_profile: Optional[dict[str, Any]] = None,
        ended_at: Optional[datetime] = None,
        inferred_scenario: Optional[str] = None,
    ) -> bool:
        """Update a test session.

        Args:
            session_id: The session ID to update.
            turn_count: New turn count (if provided).
            final_intent_profile: Final intent profile (if provided).
            ended_at: Session end timestamp (if provided).
            inferred_scenario: Inferred scenario ID (if provided).

        Returns:
            True if the session was updated, False if not found.
        """
        updates: list[str] = []
        params: list[Any] = []

        if turn_count is not None:
            updates.append("turn_count = ?")
            params.append(turn_count)

        if final_intent_profile is not None:
            updates.append("final_intent_profile = ?")
            params.append(json.dumps(final_intent_profile))

        if ended_at is not None:
            updates.append("ended_at = ?")
            params.append(ended_at.isoformat())

        if inferred_scenario is not None:
            updates.append("inferred_scenario = ?")
            params.append(inferred_scenario)

        if not updates:
            return False

        params.append(session_id)

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                f"UPDATE sessions SET {', '.join(updates)} WHERE session_id = ?",
                params,
            )
            conn.commit()
            updated = cursor.rowcount > 0

        if updated:
            logger.info(
                "session_updated",
                session_id=session_id,
                updates=updates,
            )

        return updated

    def add_turn(self, turn: ConversationTurn) -> int:
        """Add a conversation turn.

        Args:
            turn: The ConversationTurn to add.

        Returns:
            The auto-generated ID of the inserted turn.
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO turns (
                    session_id, turn_number, timestamp, user_message,
                    assistant_response, response_time_ms, tool_calls,
                    intent_profile_snapshot
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    turn.session_id,
                    turn.turn_number,
                    turn.timestamp.isoformat(),
                    turn.user_message,
                    turn.assistant_response,
                    turn.response_time_ms,
                    json.dumps(turn.tool_calls),
                    json.dumps(turn.intent_profile_snapshot),
                ),
            )
            conn.commit()
            turn_id = cursor.lastrowid

        logger.debug(
            "turn_added",
            turn_id=turn_id,
            session_id=turn.session_id,
            turn_number=turn.turn_number,
        )

        return turn_id  # type: ignore[return-value]

    def get_turns(self, session_id: str) -> list[ConversationTurn]:
        """Get all turns for a session.

        Args:
            session_id: The session ID to get turns for.

        Returns:
            List of ConversationTurn objects, ordered by turn number.
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT * FROM turns
                WHERE session_id = ?
                ORDER BY turn_number ASC
                """,
                (session_id,),
            )
            rows = cursor.fetchall()

        return [self._row_to_turn(row) for row in rows]

    def list_sessions(
        self,
        scenario_id: Optional[str] = None,
        limit: int = 100,
    ) -> list[TestSession]:
        """List test sessions.

        Args:
            scenario_id: Filter by scenario ID (optional).
            limit: Maximum number of sessions to return.

        Returns:
            List of TestSession objects, ordered by creation time (newest first).
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()

            if scenario_id is not None:
                cursor.execute(
                    """
                    SELECT * FROM sessions
                    WHERE scenario_id = ?
                    ORDER BY created_at DESC
                    LIMIT ?
                    """,
                    (scenario_id, limit),
                )
            else:
                cursor.execute(
                    """
                    SELECT * FROM sessions
                    ORDER BY created_at DESC
                    LIMIT ?
                    """,
                    (limit,),
                )

            rows = cursor.fetchall()

        return [self._row_to_session(row) for row in rows]

    def _row_to_session(self, row: sqlite3.Row) -> TestSession:
        """Convert a database row to a TestSession.

        Args:
            row: SQLite row object.

        Returns:
            TestSession object.
        """
        final_intent_profile = None
        if row["final_intent_profile"]:
            final_intent_profile = json.loads(row["final_intent_profile"])

        ended_at = None
        if row["ended_at"]:
            ended_at = datetime.fromisoformat(row["ended_at"])

        return TestSession(
            session_id=row["session_id"],
            scenario_id=row["scenario_id"],
            created_at=datetime.fromisoformat(row["created_at"]),
            ended_at=ended_at,
            final_intent_profile=final_intent_profile,
            turn_count=row["turn_count"],
            inferred_scenario=row["inferred_scenario"],
        )

    def _row_to_turn(self, row: sqlite3.Row) -> ConversationTurn:
        """Convert a database row to a ConversationTurn.

        Args:
            row: SQLite row object.

        Returns:
            ConversationTurn object.
        """
        tool_calls = []
        if row["tool_calls"]:
            tool_calls = json.loads(row["tool_calls"])

        intent_profile_snapshot = {}
        if row["intent_profile_snapshot"]:
            intent_profile_snapshot = json.loads(row["intent_profile_snapshot"])

        return ConversationTurn(
            id=row["id"],
            session_id=row["session_id"],
            turn_number=row["turn_number"],
            timestamp=datetime.fromisoformat(row["timestamp"]),
            user_message=row["user_message"],
            assistant_response=row["assistant_response"],
            response_time_ms=row["response_time_ms"],
            tool_calls=tool_calls,
            intent_profile_snapshot=intent_profile_snapshot,
        )

    def delete_session(self, session_id: str) -> bool:
        """Delete a session and all its turns.

        Args:
            session_id: The session ID to delete.

        Returns:
            True if the session was deleted, False if not found.
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            # Delete turns first (foreign key constraint)
            cursor.execute("DELETE FROM turns WHERE session_id = ?", (session_id,))
            cursor.execute("DELETE FROM sessions WHERE session_id = ?", (session_id,))
            conn.commit()
            deleted = cursor.rowcount > 0

        if deleted:
            logger.info("session_deleted", session_id=session_id)

        return deleted
