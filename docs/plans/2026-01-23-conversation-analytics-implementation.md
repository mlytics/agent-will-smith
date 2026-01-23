# Conversation Analytics Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a conversation logging system with SQLite storage and scenario-based testing UI.

**Architecture:** Two parallel tracks - Backend (Python/SQLite) and Frontend (React/TypeScript). Backend logs conversations at Agent layer; Frontend provides scenario selection via role cards.

**Tech Stack:** Python 3.14, SQLite, Pydantic, FastAPI, React, TypeScript, Tailwind CSS

---

## Parallel Execution Strategy

```
Track A (Backend)              Track B (Frontend)
────────────────               ─────────────────
Task A1: models + database     Task B1: scenarios + context
         ↓                              ↓
Task A2: logger                Task B2: selector component
         ↓                              ↓
Task A3: agent integration     Task B3: page integration
         ↓                              ↓
         └──────────┬──────────────────┘
                    ↓
            Task Final: Integration Test
```

**Shared Interface (define first):**
- Scenario format: `{ id, name, icon, shortDesc, persona }`
- API contract: `context.scenario_id` in chat request

---

## Track A: Backend

### Task A1: Models and Database

**Files:**
- Create: `src/agent_will_smith/conversation_analytics/__init__.py`
- Create: `src/agent_will_smith/conversation_analytics/models.py`
- Create: `src/agent_will_smith/conversation_analytics/database.py`
- Create: `src/agent_will_smith/conversation_analytics/scenarios.py`
- Test: `tests/conversation_analytics/test_database.py`

**Step 1: Create module structure**

Create empty `__init__.py`:

```python
# src/agent_will_smith/conversation_analytics/__init__.py
"""Conversation analytics module for logging and evaluating test conversations."""
```

**Step 2: Write models.py**

```python
# src/agent_will_smith/conversation_analytics/models.py
"""Pydantic models for conversation analytics."""

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field


class Scenario(BaseModel):
    """Predefined test scenario."""

    scenario_id: str = Field(..., description="Unique scenario identifier")
    name: str = Field(..., description="Display name")
    icon: str = Field(..., description="Emoji icon")
    short_desc: str = Field(..., description="One-line description")
    persona_description: Optional[str] = Field(None, description="Full persona text")
    expected_intents: list[str] = Field(default_factory=list)
    expected_life_stage: Optional[str] = None
    expected_risk_preference: Optional[str] = None


class TestSession(BaseModel):
    """A complete test conversation session."""

    session_id: str
    scenario_id: str
    created_at: datetime
    ended_at: Optional[datetime] = None
    final_intent_profile: Optional[dict[str, Any]] = None
    turn_count: int = 0
    inferred_scenario: Optional[str] = None


class ConversationTurn(BaseModel):
    """Single turn in a conversation."""

    id: Optional[int] = None
    session_id: str
    turn_number: int
    timestamp: datetime
    user_message: str
    assistant_response: str
    response_time_ms: int
    tool_calls: list[dict[str, Any]] = Field(default_factory=list)
    intent_profile_snapshot: dict[str, Any] = Field(default_factory=dict)
```

**Step 3: Write scenarios.py**

```python
# src/agent_will_smith/conversation_analytics/scenarios.py
"""Predefined test scenarios for conversation analytics."""

from agent_will_smith.conversation_analytics.models import Scenario

SCENARIOS: dict[str, Scenario] = {
    "cxo_wealth": Scenario(
        scenario_id="cxo_wealth",
        name="高階主管資產規劃",
        icon="👔",
        short_desc="52歲 CFO・資產規劃",
        persona_description="""你是一位 52 歲的科技公司 CFO。
- 年收入約 800 萬台幣
- 流動資產約 3000 萬
- 想在 55 歲前退休
- 對投資有經驗，但想了解更多稅務優化的方式
- 關心資產傳承和退休後的現金流""",
        expected_intents=["retirement", "wealth_management", "tax_planning"],
        expected_life_stage="pre_retirement",
        expected_risk_preference="moderate",
    ),
    "young_starter": Scenario(
        scenario_id="young_starter",
        name="年輕小資族入門",
        icon="👩‍💻",
        short_desc="28歲工程師・理財入門",
        persona_description="""你是一位 28 歲的軟體工程師。
- 月薪約 6 萬台幣
- 剛開始想理財，但不知道從何開始
- 對風險比較保守，想先存到第一桶金
- 對股票和基金有興趣但不太懂
- 希望能有系統地學習理財""",
        expected_intents=["savings", "investment_basics"],
        expected_life_stage="early_career",
        expected_risk_preference="conservative",
    ),
    "retiree_stable": Scenario(
        scenario_id="retiree_stable",
        name="退休族穩健配置",
        icon="👴",
        short_desc="62歲退休教師・穩定領息",
        persona_description="""你是一位 62 歲剛退休的高中教師。
- 有退休金每月約 5 萬
- 另有積蓄約 500 萬
- 想要穩定的被動收入
- 非常保守，不想承擔太多風險
- 關心醫療保險和長照規劃""",
        expected_intents=["income_preservation", "insurance"],
        expected_life_stage="retired",
        expected_risk_preference="conservative",
    ),
    "family_education": Scenario(
        scenario_id="family_education",
        name="雙薪家庭子女規劃",
        icon="👨‍👩‍👧",
        short_desc="38歲夫妻・教育基金",
        persona_description="""你是一對 38 歲的雙薪夫妻。
- 家庭年收入約 200 萬台幣
- 有一個 5 歲的小孩
- 想規劃小孩的教育基金
- 也關心家庭保障和房貸規劃
- 風險承受度中等""",
        expected_intents=["education_fund", "family_protection"],
        expected_life_stage="mid_career",
        expected_risk_preference="moderate",
    ),
    "free_form": Scenario(
        scenario_id="free_form",
        name="自由對話",
        icon="💬",
        short_desc="不設限・隨意聊",
        persona_description=None,
        expected_intents=[],
        expected_life_stage=None,
        expected_risk_preference=None,
    ),
}


def get_scenario(scenario_id: str) -> Scenario | None:
    """Get scenario by ID."""
    return SCENARIOS.get(scenario_id)


def get_all_scenarios() -> list[Scenario]:
    """Get all available scenarios."""
    return list(SCENARIOS.values())
```

**Step 4: Write database.py**

```python
# src/agent_will_smith/conversation_analytics/database.py
"""SQLite database for conversation analytics."""

import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any

from agent_will_smith.conversation_analytics.models import (
    ConversationTurn,
    TestSession,
)

DEFAULT_DB_PATH = Path("data/conversation_logs.db")

SCHEMA = """
CREATE TABLE IF NOT EXISTS sessions (
    session_id TEXT PRIMARY KEY,
    scenario_id TEXT NOT NULL,
    created_at TEXT NOT NULL,
    ended_at TEXT,
    final_intent_profile TEXT,
    turn_count INTEGER DEFAULT 0,
    inferred_scenario TEXT
);

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
);

CREATE INDEX IF NOT EXISTS idx_sessions_scenario ON sessions(scenario_id);
CREATE INDEX IF NOT EXISTS idx_sessions_created ON sessions(created_at);
CREATE INDEX IF NOT EXISTS idx_turns_session ON turns(session_id);
"""


class ConversationDatabase:
    """SQLite database for storing conversation logs."""

    def __init__(self, db_path: Path | str = DEFAULT_DB_PATH):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()

    def _get_connection(self) -> sqlite3.Connection:
        """Get a database connection."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_schema(self) -> None:
        """Initialize database schema."""
        with self._get_connection() as conn:
            conn.executescript(SCHEMA)
            conn.commit()

    def create_session(self, session_id: str, scenario_id: str) -> TestSession:
        """Create a new test session."""
        now = datetime.utcnow()
        session = TestSession(
            session_id=session_id,
            scenario_id=scenario_id,
            created_at=now,
        )
        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT OR IGNORE INTO sessions (session_id, scenario_id, created_at)
                VALUES (?, ?, ?)
                """,
                (session_id, scenario_id, now.isoformat()),
            )
            conn.commit()
        return session

    def get_session(self, session_id: str) -> TestSession | None:
        """Get a session by ID."""
        with self._get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM sessions WHERE session_id = ?",
                (session_id,),
            ).fetchone()
            if row:
                return TestSession(
                    session_id=row["session_id"],
                    scenario_id=row["scenario_id"],
                    created_at=datetime.fromisoformat(row["created_at"]),
                    ended_at=datetime.fromisoformat(row["ended_at"]) if row["ended_at"] else None,
                    final_intent_profile=json.loads(row["final_intent_profile"]) if row["final_intent_profile"] else None,
                    turn_count=row["turn_count"],
                    inferred_scenario=row["inferred_scenario"],
                )
        return None

    def update_session(
        self,
        session_id: str,
        turn_count: int | None = None,
        final_intent_profile: dict[str, Any] | None = None,
        ended_at: datetime | None = None,
    ) -> None:
        """Update session fields."""
        updates = []
        params = []
        if turn_count is not None:
            updates.append("turn_count = ?")
            params.append(turn_count)
        if final_intent_profile is not None:
            updates.append("final_intent_profile = ?")
            params.append(json.dumps(final_intent_profile, ensure_ascii=False))
        if ended_at is not None:
            updates.append("ended_at = ?")
            params.append(ended_at.isoformat())

        if updates:
            params.append(session_id)
            with self._get_connection() as conn:
                conn.execute(
                    f"UPDATE sessions SET {', '.join(updates)} WHERE session_id = ?",
                    params,
                )
                conn.commit()

    def add_turn(self, turn: ConversationTurn) -> int:
        """Add a conversation turn."""
        with self._get_connection() as conn:
            cursor = conn.execute(
                """
                INSERT INTO turns (
                    session_id, turn_number, timestamp, user_message,
                    assistant_response, response_time_ms, tool_calls,
                    intent_profile_snapshot
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    turn.session_id,
                    turn.turn_number,
                    turn.timestamp.isoformat(),
                    turn.user_message,
                    turn.assistant_response,
                    turn.response_time_ms,
                    json.dumps(turn.tool_calls, ensure_ascii=False),
                    json.dumps(turn.intent_profile_snapshot, ensure_ascii=False),
                ),
            )
            conn.commit()
            return cursor.lastrowid or 0

    def get_turns(self, session_id: str) -> list[ConversationTurn]:
        """Get all turns for a session."""
        with self._get_connection() as conn:
            rows = conn.execute(
                "SELECT * FROM turns WHERE session_id = ? ORDER BY turn_number",
                (session_id,),
            ).fetchall()
            return [
                ConversationTurn(
                    id=row["id"],
                    session_id=row["session_id"],
                    turn_number=row["turn_number"],
                    timestamp=datetime.fromisoformat(row["timestamp"]),
                    user_message=row["user_message"],
                    assistant_response=row["assistant_response"],
                    response_time_ms=row["response_time_ms"],
                    tool_calls=json.loads(row["tool_calls"]) if row["tool_calls"] else [],
                    intent_profile_snapshot=json.loads(row["intent_profile_snapshot"]) if row["intent_profile_snapshot"] else {},
                )
                for row in rows
            ]

    def list_sessions(
        self,
        scenario_id: str | None = None,
        limit: int = 100,
    ) -> list[TestSession]:
        """List sessions with optional filtering."""
        query = "SELECT * FROM sessions"
        params: list[Any] = []
        if scenario_id:
            query += " WHERE scenario_id = ?"
            params.append(scenario_id)
        query += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)

        with self._get_connection() as conn:
            rows = conn.execute(query, params).fetchall()
            return [
                TestSession(
                    session_id=row["session_id"],
                    scenario_id=row["scenario_id"],
                    created_at=datetime.fromisoformat(row["created_at"]),
                    ended_at=datetime.fromisoformat(row["ended_at"]) if row["ended_at"] else None,
                    final_intent_profile=json.loads(row["final_intent_profile"]) if row["final_intent_profile"] else None,
                    turn_count=row["turn_count"],
                    inferred_scenario=row["inferred_scenario"],
                )
                for row in rows
            ]
```

**Step 5: Write failing test**

Create test directory:

```python
# tests/conversation_analytics/__init__.py
```

```python
# tests/conversation_analytics/test_database.py
"""Tests for conversation analytics database."""

import tempfile
from datetime import datetime
from pathlib import Path

import pytest

from agent_will_smith.conversation_analytics.database import ConversationDatabase
from agent_will_smith.conversation_analytics.models import ConversationTurn


class TestConversationDatabase:
    """Tests for ConversationDatabase."""

    @pytest.fixture
    def db(self) -> ConversationDatabase:
        """Create a temporary database."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"
            yield ConversationDatabase(db_path)

    def test_create_session(self, db: ConversationDatabase) -> None:
        """Test creating a new session."""
        session = db.create_session("session-123", "cxo_wealth")

        assert session.session_id == "session-123"
        assert session.scenario_id == "cxo_wealth"
        assert session.turn_count == 0

    def test_get_session(self, db: ConversationDatabase) -> None:
        """Test retrieving a session."""
        db.create_session("session-456", "young_starter")

        session = db.get_session("session-456")

        assert session is not None
        assert session.scenario_id == "young_starter"

    def test_add_turn(self, db: ConversationDatabase) -> None:
        """Test adding a conversation turn."""
        db.create_session("session-789", "free_form")

        turn = ConversationTurn(
            session_id="session-789",
            turn_number=1,
            timestamp=datetime.utcnow(),
            user_message="Hello",
            assistant_response="Hi there!",
            response_time_ms=500,
            tool_calls=[{"tool": "intent_capture", "args": {}}],
            intent_profile_snapshot={"intent_score": 0.5},
        )
        turn_id = db.add_turn(turn)

        assert turn_id > 0

        turns = db.get_turns("session-789")
        assert len(turns) == 1
        assert turns[0].user_message == "Hello"
        assert turns[0].tool_calls[0]["tool"] == "intent_capture"

    def test_update_session(self, db: ConversationDatabase) -> None:
        """Test updating session fields."""
        db.create_session("session-update", "retiree_stable")

        db.update_session(
            "session-update",
            turn_count=5,
            final_intent_profile={"intent_score": 0.8},
        )

        session = db.get_session("session-update")
        assert session is not None
        assert session.turn_count == 5
        assert session.final_intent_profile["intent_score"] == 0.8

    def test_list_sessions(self, db: ConversationDatabase) -> None:
        """Test listing sessions with filtering."""
        db.create_session("s1", "cxo_wealth")
        db.create_session("s2", "cxo_wealth")
        db.create_session("s3", "young_starter")

        all_sessions = db.list_sessions()
        assert len(all_sessions) == 3

        cxo_sessions = db.list_sessions(scenario_id="cxo_wealth")
        assert len(cxo_sessions) == 2
```

**Step 6: Run tests**

```bash
uv run pytest tests/conversation_analytics/test_database.py -v
```

Expected: All tests pass.

**Step 7: Commit**

```bash
git add src/agent_will_smith/conversation_analytics/ tests/conversation_analytics/
git commit -m "feat(analytics): add conversation analytics models and database"
```

---

### Task A2: Conversation Logger

**Files:**
- Create: `src/agent_will_smith/conversation_analytics/logger.py`
- Test: `tests/conversation_analytics/test_logger.py`

**Step 1: Write logger.py**

```python
# src/agent_will_smith/conversation_analytics/logger.py
"""Conversation logger for recording test sessions."""

from datetime import datetime
from typing import Any

import structlog

from agent_will_smith.conversation_analytics.database import ConversationDatabase
from agent_will_smith.conversation_analytics.models import ConversationTurn


class ConversationLogger:
    """Logs conversation turns to the database."""

    def __init__(self, database: ConversationDatabase):
        self.db = database
        self.logger = structlog.get_logger(__name__)
        self._turn_counts: dict[str, int] = {}

    async def ensure_session(self, session_id: str, scenario_id: str) -> None:
        """Ensure a session exists, creating if necessary."""
        existing = self.db.get_session(session_id)
        if not existing:
            self.db.create_session(session_id, scenario_id)
            self._turn_counts[session_id] = 0
            self.logger.info(
                "created new session",
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
        """Log a single conversation turn."""
        turn_number = self._turn_counts.get(session_id, 0) + 1
        self._turn_counts[session_id] = turn_number

        turn = ConversationTurn(
            session_id=session_id,
            turn_number=turn_number,
            timestamp=datetime.utcnow(),
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
            "logged conversation turn",
            session_id=session_id,
            turn_number=turn_number,
            response_time_ms=response_time_ms,
            tool_calls_count=len(tool_calls),
        )

    async def end_session(self, session_id: str) -> None:
        """Mark a session as ended."""
        self.db.update_session(session_id, ended_at=datetime.utcnow())
        self.logger.info("ended session", session_id=session_id)
```

**Step 2: Write test**

```python
# tests/conversation_analytics/test_logger.py
"""Tests for conversation logger."""

import tempfile
from pathlib import Path

import pytest

from agent_will_smith.conversation_analytics.database import ConversationDatabase
from agent_will_smith.conversation_analytics.logger import ConversationLogger


class TestConversationLogger:
    """Tests for ConversationLogger."""

    @pytest.fixture
    def logger(self) -> ConversationLogger:
        """Create a logger with temporary database."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"
            db = ConversationDatabase(db_path)
            yield ConversationLogger(db)

    @pytest.mark.asyncio
    async def test_ensure_session_creates_new(self, logger: ConversationLogger) -> None:
        """Test that ensure_session creates a new session."""
        await logger.ensure_session("new-session", "cxo_wealth")

        session = logger.db.get_session("new-session")
        assert session is not None
        assert session.scenario_id == "cxo_wealth"

    @pytest.mark.asyncio
    async def test_ensure_session_idempotent(self, logger: ConversationLogger) -> None:
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
```

**Step 3: Run tests**

```bash
uv run pytest tests/conversation_analytics/test_logger.py -v
```

Expected: All tests pass.

**Step 4: Commit**

```bash
git add src/agent_will_smith/conversation_analytics/logger.py tests/conversation_analytics/test_logger.py
git commit -m "feat(analytics): add ConversationLogger for recording turns"
```

---

### Task A3: Agent Integration

**Files:**
- Modify: `src/agent_will_smith/agent/intent_chat/agent.py`
- Modify: `src/agent_will_smith/agent/intent_chat/container.py`
- Test: `tests/agent/intent_chat/test_agent.py` (add test)

**Step 1: Modify container.py to provide logger**

Add to `container.py`:

```python
# Add imports at top
from agent_will_smith.conversation_analytics.database import ConversationDatabase
from agent_will_smith.conversation_analytics.logger import ConversationLogger

# Add providers in Container class
class Container(containers.DeclarativeContainer):
    # ... existing providers ...

    # Conversation analytics (optional - only if enabled)
    conversation_database = providers.Singleton(
        ConversationDatabase,
    )

    conversation_logger = providers.Singleton(
        ConversationLogger,
        database=conversation_database,
    )
```

**Step 2: Modify agent.py to use logger**

Update `Agent.__init__` and `invoke`:

```python
# In agent.py, modify __init__ signature
def __init__(
    self,
    # ... existing params ...
    conversation_logger: ConversationLogger | None = None,
):
    # ... existing init ...
    self.conversation_logger = conversation_logger

# In invoke method, add logging
async def invoke(self, input_dto: ChatInput) -> ChatOutput:
    import time
    start_time = time.time()

    # Ensure session exists if logging enabled
    if self.conversation_logger:
        scenario_id = "free_form"
        if input_dto.context and "scenario_id" in input_dto.context:
            scenario_id = input_dto.context["scenario_id"]
        await self.conversation_logger.ensure_session(
            session_id=input_dto.session_id,
            scenario_id=scenario_id,
        )

    # ... existing invoke logic ...
    # (run graph, get output)

    # Log turn if enabled
    if self.conversation_logger:
        response_time_ms = int((time.time() - start_time) * 1000)
        await self.conversation_logger.log_turn(
            session_id=input_dto.session_id,
            user_message=input_dto.message,
            assistant_response=output.response,
            response_time_ms=response_time_ms,
            tool_calls=output.tool_calls,
            intent_profile=output.intent_profile.model_dump(),
        )

    return output
```

**Step 3: Update container to wire logger to agent**

```python
# In container.py, update agent provider
agent = providers.Factory(
    Agent,
    # ... existing params ...
    conversation_logger=conversation_logger,
)
```

**Step 4: Add test for logging integration**

Add to existing `test_agent.py` or create new test:

```python
# tests/agent/intent_chat/test_agent_logging.py
"""Tests for agent conversation logging integration."""

import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest

from agent_will_smith.conversation_analytics.database import ConversationDatabase
from agent_will_smith.conversation_analytics.logger import ConversationLogger


class TestAgentLogging:
    """Tests for agent logging integration."""

    @pytest.mark.asyncio
    async def test_agent_logs_turn_when_logger_provided(self) -> None:
        """Test that agent logs turn when conversation_logger is provided."""
        # Create mock logger
        mock_logger = AsyncMock(spec=ConversationLogger)

        # This test verifies the integration pattern
        # Full integration test requires actual agent setup
        await mock_logger.ensure_session("test-session", "cxo_wealth")
        await mock_logger.log_turn(
            session_id="test-session",
            user_message="Hello",
            assistant_response="Hi!",
            response_time_ms=100,
            tool_calls=[],
            intent_profile={"intent_score": 0.5},
        )

        mock_logger.ensure_session.assert_called_once()
        mock_logger.log_turn.assert_called_once()
```

**Step 5: Run tests**

```bash
uv run pytest tests/agent/intent_chat/test_agent_logging.py -v
uv run pytest tests/conversation_analytics/ -v
```

Expected: All tests pass.

**Step 6: Commit**

```bash
git add src/agent_will_smith/agent/intent_chat/agent.py \
        src/agent_will_smith/agent/intent_chat/container.py \
        tests/agent/intent_chat/test_agent_logging.py
git commit -m "feat(analytics): integrate ConversationLogger into Agent"
```

---

## Track B: Frontend

### Task B1: Scenarios Definition and Context

**Files:**
- Create: `frontend/lib/scenarios.ts`
- Create: `frontend/lib/scenario-context.tsx`

**Step 1: Create scenarios.ts**

```typescript
// frontend/lib/scenarios.ts

export interface Scenario {
  id: string;
  name: string;
  icon: string;
  shortDesc: string;
  persona: string | null;
}

export const SCENARIOS: Scenario[] = [
  {
    id: "cxo_wealth",
    name: "高階主管資產規劃",
    icon: "👔",
    shortDesc: "52歲 CFO・資產規劃",
    persona: `你是一位 52 歲的科技公司 CFO。
• 年收入約 800 萬台幣
• 流動資產約 3000 萬
• 想在 55 歲前退休
• 對投資有經驗，但想了解更多稅務優化的方式
• 關心資產傳承和退休後的現金流`,
  },
  {
    id: "young_starter",
    name: "年輕小資族入門",
    icon: "👩‍💻",
    shortDesc: "28歲工程師・理財入門",
    persona: `你是一位 28 歲的軟體工程師。
• 月薪約 6 萬台幣
• 剛開始想理財，但不知道從何開始
• 對風險比較保守，想先存到第一桶金
• 對股票和基金有興趣但不太懂
• 希望能有系統地學習理財`,
  },
  {
    id: "retiree_stable",
    name: "退休族穩健配置",
    icon: "👴",
    shortDesc: "62歲退休教師・穩定領息",
    persona: `你是一位 62 歲剛退休的高中教師。
• 有退休金每月約 5 萬
• 另有積蓄約 500 萬
• 想要穩定的被動收入
• 非常保守，不想承擔太多風險
• 關心醫療保險和長照規劃`,
  },
  {
    id: "family_education",
    name: "雙薪家庭子女規劃",
    icon: "👨‍👩‍👧",
    shortDesc: "38歲夫妻・教育基金",
    persona: `你是一對 38 歲的雙薪夫妻。
• 家庭年收入約 200 萬台幣
• 有一個 5 歲的小孩
• 想規劃小孩的教育基金
• 也關心家庭保障和房貸規劃
• 風險承受度中等`,
  },
  {
    id: "free_form",
    name: "自由對話",
    icon: "💬",
    shortDesc: "不設限・隨意聊",
    persona: null,
  },
];

export function getScenario(id: string): Scenario | undefined {
  return SCENARIOS.find((s) => s.id === id);
}
```

**Step 2: Create scenario-context.tsx**

```typescript
// frontend/lib/scenario-context.tsx
"use client";

import {
  createContext,
  useContext,
  useState,
  useCallback,
  type ReactNode,
} from "react";
import { SCENARIOS, type Scenario } from "./scenarios";

interface ScenarioContextType {
  selectedScenario: Scenario;
  setScenario: (scenarioId: string) => void;
  resetScenario: () => void;
}

const defaultScenario = SCENARIOS.find((s) => s.id === "free_form")!;

const ScenarioContext = createContext<ScenarioContextType | null>(null);

export function ScenarioProvider({ children }: { children: ReactNode }) {
  const [selectedScenario, setSelectedScenario] =
    useState<Scenario>(defaultScenario);

  const setScenario = useCallback((scenarioId: string) => {
    const scenario = SCENARIOS.find((s) => s.id === scenarioId);
    if (scenario) {
      setSelectedScenario(scenario);
    }
  }, []);

  const resetScenario = useCallback(() => {
    setSelectedScenario(defaultScenario);
  }, []);

  return (
    <ScenarioContext.Provider
      value={{ selectedScenario, setScenario, resetScenario }}
    >
      {children}
    </ScenarioContext.Provider>
  );
}

export function useScenario() {
  const context = useContext(ScenarioContext);
  if (!context) {
    throw new Error("useScenario must be used within ScenarioProvider");
  }
  return context;
}
```

**Step 3: Verify TypeScript compiles**

```bash
cd frontend && npm run build
```

Expected: Build succeeds.

**Step 4: Commit**

```bash
git add frontend/lib/scenarios.ts frontend/lib/scenario-context.tsx
git commit -m "feat(frontend): add scenario definitions and context"
```

---

### Task B2: Scenario Selector Component

**Files:**
- Create: `frontend/components/assistant-ui/scenario-selector.tsx`

**Step 1: Create scenario-selector.tsx**

```typescript
// frontend/components/assistant-ui/scenario-selector.tsx
"use client";

import { useState } from "react";
import { Card } from "@/components/ui/card";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible";
import { ChevronDownIcon, FlaskConicalIcon } from "lucide-react";
import { cn } from "@/lib/utils";
import { useScenario } from "@/lib/scenario-context";
import { SCENARIOS, type Scenario } from "@/lib/scenarios";

function ScenarioCard({
  scenario,
  isSelected,
  onSelect,
}: {
  scenario: Scenario;
  isSelected: boolean;
  onSelect: () => void;
}) {
  return (
    <TooltipProvider>
      <Tooltip>
        <TooltipTrigger asChild>
          <Card
            className={cn(
              "cursor-pointer p-3 transition-all hover:shadow-md",
              "flex flex-col items-center text-center gap-1 min-w-[100px]",
              isSelected
                ? "ring-2 ring-amber-500 bg-amber-50 dark:bg-amber-950/30"
                : "hover:bg-secondary/50"
            )}
            onClick={onSelect}
          >
            <span className="text-2xl">{scenario.icon}</span>
            <span className="text-xs font-medium leading-tight">
              {scenario.name}
            </span>
            <span className="text-[10px] text-muted-foreground leading-tight">
              {scenario.shortDesc}
            </span>
          </Card>
        </TooltipTrigger>
        {scenario.persona && (
          <TooltipContent side="bottom" className="max-w-xs">
            <p className="text-xs whitespace-pre-line">{scenario.persona}</p>
          </TooltipContent>
        )}
      </Tooltip>
    </TooltipProvider>
  );
}

export function ScenarioSelector() {
  const [isOpen, setIsOpen] = useState(true);
  const { selectedScenario, setScenario } = useScenario();

  // Split scenarios: main row (4) + second row (1: free_form)
  const mainScenarios = SCENARIOS.filter((s) => s.id !== "free_form");
  const freeFormScenario = SCENARIOS.find((s) => s.id === "free_form")!;

  return (
    <Collapsible open={isOpen} onOpenChange={setIsOpen}>
      <CollapsibleTrigger asChild>
        <div className="flex items-center justify-between px-2 py-2 cursor-pointer hover:bg-secondary/30 rounded-lg transition-colors">
          <div className="flex items-center gap-2">
            <FlaskConicalIcon className="h-4 w-4 text-muted-foreground" />
            <span className="text-sm font-medium">測試情境</span>
            <span className="text-xs text-muted-foreground">
              {selectedScenario.name}
            </span>
          </div>
          <ChevronDownIcon
            className={cn(
              "h-4 w-4 text-muted-foreground transition-transform",
              isOpen && "rotate-180"
            )}
          />
        </div>
      </CollapsibleTrigger>

      <CollapsibleContent>
        <div className="pt-2 pb-4 space-y-3">
          {/* Main scenarios row */}
          <div className="flex flex-wrap gap-2 justify-center">
            {mainScenarios.map((scenario) => (
              <ScenarioCard
                key={scenario.id}
                scenario={scenario}
                isSelected={selectedScenario.id === scenario.id}
                onSelect={() => setScenario(scenario.id)}
              />
            ))}
          </div>

          {/* Free form centered below */}
          <div className="flex justify-center">
            <ScenarioCard
              scenario={freeFormScenario}
              isSelected={selectedScenario.id === freeFormScenario.id}
              onSelect={() => setScenario(freeFormScenario.id)}
            />
          </div>

          {/* Persona hint if selected */}
          {selectedScenario.persona && (
            <div className="mx-auto max-w-md p-3 rounded-lg bg-secondary/50 text-xs text-muted-foreground">
              <p className="font-medium text-foreground mb-1">角色設定：</p>
              <p className="whitespace-pre-line">{selectedScenario.persona}</p>
            </div>
          )}
        </div>
      </CollapsibleContent>
    </Collapsible>
  );
}
```

**Step 2: Verify TypeScript compiles**

```bash
cd frontend && npm run build
```

Expected: Build succeeds.

**Step 3: Commit**

```bash
git add frontend/components/assistant-ui/scenario-selector.tsx
git commit -m "feat(frontend): add ScenarioSelector component with role cards"
```

---

### Task B3: Page Integration

**Files:**
- Modify: `frontend/lib/runtime-provider.tsx`
- Modify: `frontend/app/page.tsx`

**Step 1: Update runtime-provider.tsx to include ScenarioProvider and pass scenario_id**

Wrap with `ScenarioProvider` and pass `scenario_id` in context:

```typescript
// In runtime-provider.tsx

// Add import
import { ScenarioProvider, useScenario } from "./scenario-context";

// Modify RuntimeProviderInner to use scenario
function RuntimeProviderInner({ children }: { children: ReactNode }) {
  // ... existing state ...
  const { selectedScenario } = useScenario();

  // In streamMessage call, add scenario_id to context:
  await streamMessage(
    messageText,
    sessionId,
    messages,
    {
      // ... callbacks ...
    },
    profile,
    { scenario_id: selectedScenario.id }  // Add this parameter
  );
}

// Update RuntimeProvider to include ScenarioProvider
export function RuntimeProvider({ children }: { children: ReactNode }) {
  return (
    <ScenarioProvider>
      <IntentProfileProvider>
        <RuntimeProviderInner>{children}</RuntimeProviderInner>
      </IntentProfileProvider>
    </ScenarioProvider>
  );
}
```

**Step 2: Update chat-api.ts to accept context parameter**

```typescript
// In chat-api.ts, update streamMessage signature
export async function streamMessage(
  message: string,
  sessionId: string,
  conversationHistory: Message[],
  callbacks: StreamCallbacks,
  intentProfile?: IntentProfile | null,
  context?: Record<string, string>  // Add this
): Promise<void> {
  // ...
  body: JSON.stringify({
    message,
    session_id: sessionId,
    conversation_history: history,
    intent_profile: intentProfile || undefined,
    context: context || undefined,  // Add this
  }),
}
```

**Step 3: Update page.tsx to include ScenarioSelector**

```typescript
// In app/page.tsx, add ScenarioSelector above Thread

import { ScenarioSelector } from "@/components/assistant-ui/scenario-selector";

export default function Home() {
  return (
    <main className="...">
      {/* Left: Chat */}
      <div className="...">
        <ScenarioSelector />  {/* Add this */}
        <Thread />
      </div>

      {/* Right: Intent Profile Panel */}
      {/* ... */}
    </main>
  );
}
```

**Step 4: Verify build**

```bash
cd frontend && npm run build
```

Expected: Build succeeds.

**Step 5: Commit**

```bash
git add frontend/lib/runtime-provider.tsx \
        frontend/lib/chat-api.ts \
        frontend/app/page.tsx
git commit -m "feat(frontend): integrate ScenarioSelector into page"
```

---

## Task Final: Integration Test

**After both tracks complete:**

**Step 1: Start backend**

```bash
uv run uvicorn agent_will_smith.main:app --reload --host 0.0.0.0 --port 8000
```

**Step 2: Start frontend**

```bash
cd frontend && npm run dev
```

**Step 3: Manual test checklist**

- [ ] Select "高階主管資產規劃" scenario
- [ ] Send a message about retirement planning
- [ ] Verify in SQLite that session is created with `scenario_id = cxo_wealth`
- [ ] Verify turn is logged with correct fields
- [ ] Switch to "自由對話" and send another message
- [ ] Verify new session with `scenario_id = free_form`

**Step 4: Check SQLite data**

```bash
sqlite3 data/conversation_logs.db "SELECT * FROM sessions;"
sqlite3 data/conversation_logs.db "SELECT session_id, turn_number, user_message FROM turns;"
```

**Step 5: Final commit**

```bash
git add -A
git commit -m "feat(analytics): complete conversation analytics MVP"
```

---

## Summary

| Track | Tasks | Est. Time |
|-------|-------|-----------|
| A (Backend) | A1: models + database, A2: logger, A3: agent integration | 1.5 days |
| B (Frontend) | B1: scenarios + context, B2: selector, B3: page integration | 1 day |
| Final | Integration test | 0.5 day |

**Total: ~3 days with 2 parallel agents**
