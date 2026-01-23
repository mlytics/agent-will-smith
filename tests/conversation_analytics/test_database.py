"""Tests for conversation analytics database."""

import tempfile
from datetime import datetime, timezone
from pathlib import Path

import pytest
from pydantic import ValidationError

from agent_will_smith.conversation_analytics.database import ConversationDatabase
from agent_will_smith.conversation_analytics.models import (
    ConversationTurn,
    Scenario,
    TestSession,
)
from agent_will_smith.conversation_analytics.scenarios import (
    CXO_WEALTH,
    FREE_FORM,
    SCENARIOS,
    get_scenario,
    list_scenarios,
)


class TestScenarioModel:
    """Tests for Scenario Pydantic model."""

    def test_scenario_creates_with_required_fields(self):
        """Scenario should create with all required fields."""
        scenario = Scenario(
            scenario_id="test_scenario",
            name="Test Scenario",
            icon="test",
            short_desc="A test scenario",
        )

        assert scenario.scenario_id == "test_scenario"
        assert scenario.name == "Test Scenario"
        assert scenario.icon == "test"
        assert scenario.short_desc == "A test scenario"
        assert scenario.persona_description is None
        assert scenario.expected_intents == []
        assert scenario.expected_life_stage is None
        assert scenario.expected_risk_preference is None

    def test_scenario_creates_with_all_fields(self):
        """Scenario should accept all optional fields."""
        scenario = Scenario(
            scenario_id="full_scenario",
            name="Full Scenario",
            icon="star",
            short_desc="A complete scenario",
            persona_description="You are a test persona",
            expected_intents=["retirement", "investment"],
            expected_life_stage="mid_career",
            expected_risk_preference="moderate",
        )

        assert scenario.persona_description == "You are a test persona"
        assert scenario.expected_intents == ["retirement", "investment"]
        assert scenario.expected_life_stage == "mid_career"
        assert scenario.expected_risk_preference == "moderate"

    def test_scenario_validates_scenario_id_not_empty(self):
        """Scenario scenario_id must not be empty."""
        with pytest.raises(ValidationError):
            Scenario(
                scenario_id="",
                name="Test",
                icon="test",
                short_desc="Test",
            )

    def test_scenario_validates_name_not_empty(self):
        """Scenario name must not be empty."""
        with pytest.raises(ValidationError):
            Scenario(
                scenario_id="test",
                name="",
                icon="test",
                short_desc="Test",
            )


class TestTestSessionModel:
    """Tests for TestSession Pydantic model."""

    def test_test_session_creates_with_required_fields(self):
        """TestSession should create with required fields."""
        now = datetime.now(timezone.utc)
        session = TestSession(
            session_id="test-session-123",
            scenario_id="cxo_wealth",
            created_at=now,
        )

        assert session.session_id == "test-session-123"
        assert session.scenario_id == "cxo_wealth"
        assert session.created_at == now
        assert session.ended_at is None
        assert session.final_intent_profile is None
        assert session.turn_count == 0
        assert session.inferred_scenario is None

    def test_test_session_creates_with_all_fields(self):
        """TestSession should accept all optional fields."""
        now = datetime.now(timezone.utc)
        session = TestSession(
            session_id="test-session-456",
            scenario_id="young_starter",
            created_at=now,
            ended_at=now,
            final_intent_profile={"life_stage": "early_career"},
            turn_count=5,
            inferred_scenario="young_starter",
        )

        assert session.ended_at == now
        assert session.final_intent_profile == {"life_stage": "early_career"}
        assert session.turn_count == 5
        assert session.inferred_scenario == "young_starter"

    def test_test_session_validates_turn_count_non_negative(self):
        """TestSession turn_count must be non-negative."""
        with pytest.raises(ValidationError):
            TestSession(
                session_id="test",
                scenario_id="test",
                created_at=datetime.now(timezone.utc),
                turn_count=-1,
            )


class TestConversationTurnModel:
    """Tests for ConversationTurn Pydantic model."""

    def test_conversation_turn_creates_with_required_fields(self):
        """ConversationTurn should create with required fields."""
        now = datetime.now(timezone.utc)
        turn = ConversationTurn(
            session_id="session-123",
            turn_number=1,
            timestamp=now,
            user_message="Hello, I need financial advice",
            assistant_response="Hello! I'd be happy to help.",
            response_time_ms=250,
        )

        assert turn.id is None
        assert turn.session_id == "session-123"
        assert turn.turn_number == 1
        assert turn.timestamp == now
        assert turn.user_message == "Hello, I need financial advice"
        assert turn.assistant_response == "Hello! I'd be happy to help."
        assert turn.response_time_ms == 250
        assert turn.tool_calls == []
        assert turn.intent_profile_snapshot == {}

    def test_conversation_turn_creates_with_all_fields(self):
        """ConversationTurn should accept all optional fields."""
        now = datetime.now(timezone.utc)
        turn = ConversationTurn(
            id=42,
            session_id="session-456",
            turn_number=3,
            timestamp=now,
            user_message="What about retirement?",
            assistant_response="Great question about retirement!",
            response_time_ms=500,
            tool_calls=[{"tool": "intent_capture", "captured": True}],
            intent_profile_snapshot={"life_stage": "pre_retirement"},
        )

        assert turn.id == 42
        assert turn.tool_calls == [{"tool": "intent_capture", "captured": True}]
        assert turn.intent_profile_snapshot == {"life_stage": "pre_retirement"}

    def test_conversation_turn_validates_turn_number_positive(self):
        """ConversationTurn turn_number must be positive."""
        with pytest.raises(ValidationError):
            ConversationTurn(
                session_id="test",
                turn_number=0,
                timestamp=datetime.now(timezone.utc),
                user_message="Hello",
                assistant_response="Hi",
                response_time_ms=100,
            )

    def test_conversation_turn_validates_response_time_non_negative(self):
        """ConversationTurn response_time_ms must be non-negative."""
        with pytest.raises(ValidationError):
            ConversationTurn(
                session_id="test",
                turn_number=1,
                timestamp=datetime.now(timezone.utc),
                user_message="Hello",
                assistant_response="Hi",
                response_time_ms=-1,
            )

    def test_conversation_turn_validates_user_message_not_empty(self):
        """ConversationTurn user_message must not be empty."""
        with pytest.raises(ValidationError):
            ConversationTurn(
                session_id="test",
                turn_number=1,
                timestamp=datetime.now(timezone.utc),
                user_message="",
                assistant_response="Hi",
                response_time_ms=100,
            )


class TestPredefinedScenarios:
    """Tests for predefined scenarios."""

    def test_cxo_wealth_scenario_has_correct_attributes(self):
        """CXO wealth scenario should have correct attributes."""
        assert CXO_WEALTH.scenario_id == "cxo_wealth"
        assert CXO_WEALTH.name == "High-Level Executive Wealth Planning"
        assert CXO_WEALTH.icon == "briefcase"
        assert "CFO" in CXO_WEALTH.persona_description
        assert "retirement" in CXO_WEALTH.expected_intents
        assert CXO_WEALTH.expected_life_stage == "pre_retirement"
        assert CXO_WEALTH.expected_risk_preference == "moderate"

    def test_free_form_scenario_has_no_expectations(self):
        """Free form scenario should have no predefined expectations."""
        assert FREE_FORM.scenario_id == "free_form"
        assert FREE_FORM.persona_description is None
        assert FREE_FORM.expected_intents == []
        assert FREE_FORM.expected_life_stage is None
        assert FREE_FORM.expected_risk_preference is None

    def test_scenarios_dict_contains_all_scenarios(self):
        """SCENARIOS dict should contain all 5 predefined scenarios."""
        assert len(SCENARIOS) == 5
        assert "cxo_wealth" in SCENARIOS
        assert "young_starter" in SCENARIOS
        assert "retiree_stable" in SCENARIOS
        assert "family_education" in SCENARIOS
        assert "free_form" in SCENARIOS

    def test_get_scenario_returns_correct_scenario(self):
        """get_scenario should return the correct scenario by ID."""
        scenario = get_scenario("young_starter")
        assert scenario is not None
        assert scenario.scenario_id == "young_starter"
        assert scenario.expected_risk_preference == "aggressive"

    def test_get_scenario_returns_none_for_unknown_id(self):
        """get_scenario should return None for unknown ID."""
        assert get_scenario("unknown_scenario") is None

    def test_list_scenarios_returns_all_scenarios(self):
        """list_scenarios should return all predefined scenarios."""
        scenarios = list_scenarios()
        assert len(scenarios) == 5
        scenario_ids = {s.scenario_id for s in scenarios}
        assert scenario_ids == {"cxo_wealth", "young_starter", "retiree_stable", "family_education", "free_form"}


class TestConversationDatabase:
    """Tests for ConversationDatabase."""

    @pytest.fixture
    def db(self) -> ConversationDatabase:
        """Create a temporary database for testing."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name
        db = ConversationDatabase(db_path)
        yield db
        # Cleanup
        Path(db_path).unlink(missing_ok=True)

    def test_create_session_returns_test_session(self, db: ConversationDatabase):
        """create_session should return a TestSession with correct values."""
        session = db.create_session("session-001", "cxo_wealth")

        assert session.session_id == "session-001"
        assert session.scenario_id == "cxo_wealth"
        assert session.turn_count == 0
        assert session.ended_at is None
        assert session.final_intent_profile is None
        assert isinstance(session.created_at, datetime)

    def test_get_session_returns_session(self, db: ConversationDatabase):
        """get_session should return the session by ID."""
        db.create_session("session-002", "young_starter")
        session = db.get_session("session-002")

        assert session is not None
        assert session.session_id == "session-002"
        assert session.scenario_id == "young_starter"

    def test_get_session_returns_none_for_missing(self, db: ConversationDatabase):
        """get_session should return None for non-existent session."""
        session = db.get_session("nonexistent-session")
        assert session is None

    def test_update_session_updates_turn_count(self, db: ConversationDatabase):
        """update_session should update turn_count."""
        db.create_session("session-003", "retiree_stable")
        updated = db.update_session("session-003", turn_count=5)

        assert updated is True
        session = db.get_session("session-003")
        assert session.turn_count == 5

    def test_update_session_updates_final_intent_profile(self, db: ConversationDatabase):
        """update_session should update final_intent_profile."""
        db.create_session("session-004", "family_education")
        profile = {"life_stage": "mid_career", "risk_preference": "moderate"}
        db.update_session("session-004", final_intent_profile=profile)

        session = db.get_session("session-004")
        assert session.final_intent_profile == profile

    def test_update_session_updates_ended_at(self, db: ConversationDatabase):
        """update_session should update ended_at."""
        db.create_session("session-005", "free_form")
        end_time = datetime.now(timezone.utc)
        db.update_session("session-005", ended_at=end_time)

        session = db.get_session("session-005")
        assert session.ended_at is not None
        # Compare ISO format strings (SQLite stores as text)
        assert session.ended_at.isoformat() == end_time.isoformat()

    def test_update_session_updates_inferred_scenario(self, db: ConversationDatabase):
        """update_session should update inferred_scenario."""
        db.create_session("session-006", "free_form")
        db.update_session("session-006", inferred_scenario="young_starter")

        session = db.get_session("session-006")
        assert session.inferred_scenario == "young_starter"

    def test_update_session_returns_false_for_missing(self, db: ConversationDatabase):
        """update_session should return False for non-existent session."""
        updated = db.update_session("nonexistent", turn_count=1)
        assert updated is False

    def test_update_session_returns_false_for_no_updates(self, db: ConversationDatabase):
        """update_session should return False when no fields provided."""
        db.create_session("session-007", "cxo_wealth")
        updated = db.update_session("session-007")
        assert updated is False

    def test_add_turn_returns_id(self, db: ConversationDatabase):
        """add_turn should return the auto-generated ID."""
        db.create_session("session-008", "young_starter")
        turn = ConversationTurn(
            session_id="session-008",
            turn_number=1,
            timestamp=datetime.now(timezone.utc),
            user_message="Hello!",
            assistant_response="Hi there!",
            response_time_ms=150,
        )
        turn_id = db.add_turn(turn)

        assert turn_id is not None
        assert turn_id > 0

    def test_add_turn_stores_tool_calls_and_snapshot(self, db: ConversationDatabase):
        """add_turn should store tool_calls and intent_profile_snapshot."""
        db.create_session("session-009", "retiree_stable")
        turn = ConversationTurn(
            session_id="session-009",
            turn_number=1,
            timestamp=datetime.now(timezone.utc),
            user_message="I want stable income",
            assistant_response="I understand you want stable income.",
            response_time_ms=300,
            tool_calls=[{"tool": "intent_capture", "intent": "income_generation"}],
            intent_profile_snapshot={"life_stage": "retired"},
        )
        db.add_turn(turn)

        turns = db.get_turns("session-009")
        assert len(turns) == 1
        assert turns[0].tool_calls == [{"tool": "intent_capture", "intent": "income_generation"}]
        assert turns[0].intent_profile_snapshot == {"life_stage": "retired"}

    def test_get_turns_returns_ordered_list(self, db: ConversationDatabase):
        """get_turns should return turns ordered by turn_number."""
        db.create_session("session-010", "family_education")
        now = datetime.now(timezone.utc)

        # Add turns in reverse order
        for i in [3, 1, 2]:
            turn = ConversationTurn(
                session_id="session-010",
                turn_number=i,
                timestamp=now,
                user_message=f"Message {i}",
                assistant_response=f"Response {i}",
                response_time_ms=100 * i,
            )
            db.add_turn(turn)

        turns = db.get_turns("session-010")
        assert len(turns) == 3
        assert turns[0].turn_number == 1
        assert turns[1].turn_number == 2
        assert turns[2].turn_number == 3

    def test_get_turns_returns_empty_for_no_turns(self, db: ConversationDatabase):
        """get_turns should return empty list for session with no turns."""
        db.create_session("session-011", "cxo_wealth")
        turns = db.get_turns("session-011")
        assert turns == []

    def test_get_turns_returns_empty_for_missing_session(self, db: ConversationDatabase):
        """get_turns should return empty list for non-existent session."""
        turns = db.get_turns("nonexistent-session")
        assert turns == []

    def test_list_sessions_returns_all_sessions(self, db: ConversationDatabase):
        """list_sessions should return all sessions."""
        db.create_session("session-012", "cxo_wealth")
        db.create_session("session-013", "young_starter")
        db.create_session("session-014", "retiree_stable")

        sessions = db.list_sessions()
        assert len(sessions) == 3

    def test_list_sessions_filters_by_scenario_id(self, db: ConversationDatabase):
        """list_sessions should filter by scenario_id when provided."""
        db.create_session("session-015", "cxo_wealth")
        db.create_session("session-016", "young_starter")
        db.create_session("session-017", "cxo_wealth")

        sessions = db.list_sessions(scenario_id="cxo_wealth")
        assert len(sessions) == 2
        assert all(s.scenario_id == "cxo_wealth" for s in sessions)

    def test_list_sessions_respects_limit(self, db: ConversationDatabase):
        """list_sessions should respect the limit parameter."""
        for i in range(10):
            db.create_session(f"session-limit-{i}", "free_form")

        sessions = db.list_sessions(limit=5)
        assert len(sessions) == 5

    def test_list_sessions_orders_by_created_at_desc(self, db: ConversationDatabase):
        """list_sessions should order by created_at descending (newest first)."""
        db.create_session("session-old", "cxo_wealth")
        db.create_session("session-new", "young_starter")

        sessions = db.list_sessions()
        # Newest first
        assert sessions[0].session_id == "session-new"
        assert sessions[1].session_id == "session-old"

    def test_delete_session_removes_session_and_turns(self, db: ConversationDatabase):
        """delete_session should remove the session and all its turns."""
        db.create_session("session-delete", "family_education")
        turn = ConversationTurn(
            session_id="session-delete",
            turn_number=1,
            timestamp=datetime.now(timezone.utc),
            user_message="Hello",
            assistant_response="Hi",
            response_time_ms=100,
        )
        db.add_turn(turn)

        deleted = db.delete_session("session-delete")

        assert deleted is True
        assert db.get_session("session-delete") is None
        assert db.get_turns("session-delete") == []

    def test_delete_session_returns_false_for_missing(self, db: ConversationDatabase):
        """delete_session should return False for non-existent session."""
        deleted = db.delete_session("nonexistent-session")
        assert deleted is False

    def test_database_creates_file(self):
        """Database should create the SQLite file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"
            ConversationDatabase(db_path)
            assert db_path.exists()

    def test_database_schema_is_idempotent(self):
        """Initializing database twice should not fail."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name

        try:
            # Initialize twice
            ConversationDatabase(db_path)
            db2 = ConversationDatabase(db_path)

            # Should still work
            session = db2.create_session("idempotent-test", "free_form")
            assert session.session_id == "idempotent-test"
        finally:
            Path(db_path).unlink(missing_ok=True)
