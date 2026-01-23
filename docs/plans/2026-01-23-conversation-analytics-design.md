# Conversation Analytics System - Design Document

## Overview

A system to record, analyze, and evaluate test conversations from the Intent Chat POC. Enables systematic testing with predefined scenarios and builds foundation for AI evaluation.

## Goals

1. Record all test conversations (prompts, responses, tool calls, intent profiles)
2. Support both predefined scenarios (personas) and free-form testing
3. Store data in SQLite for easy querying and future dashboard integration
4. Enable evaluation of: intent accuracy, conversation fluency, recommendation relevance

## Design Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Logging layer | Agent layer | Captures all invocations regardless of API endpoint |
| Storage | SQLite | Easy querying, single file, dashboard-ready |
| UI for scenarios | Role cards | Visual, engaging, supports persona immersion |
| Scenario count | 4 predefined + 1 free | Covers key life stages and risk profiles |

## Scenarios

| ID | Name | Persona | Expected Intents | Life Stage |
|----|------|---------|------------------|------------|
| `cxo_wealth` | 高階主管資產規劃 | 52歲科技業CFO，年收入800萬，流動資產3000萬，想55歲退休 | retirement, wealth_management, tax_planning | pre_retirement |
| `young_starter` | 年輕小資族入門 | 28歲工程師，月薪6萬，剛開始理財，想存第一桶金 | savings, investment_basics | early_career |
| `retiree_stable` | 退休族穩健配置 | 62歲剛退休教師，有退休金+500萬積蓄，想穩定領息 | income_preservation, insurance | retired |
| `family_education` | 雙薪家庭子女規劃 | 38歲夫妻，家庭年收入200萬，小孩5歲，想規劃教育基金 | education_fund, family_protection | mid_career |
| `free_form` | 自由對話 | 無限制，測試者自由發揮 | (AI auto-classify) | (AI infer) |

## Data Models

### Python (Backend)

```python
class Scenario(BaseModel):
    scenario_id: str
    name: str
    icon: str
    short_desc: str
    persona_description: str | None
    expected_intents: list[str]
    expected_life_stage: str | None
    expected_risk_preference: str | None

class TestSession(BaseModel):
    session_id: str
    scenario_id: str
    created_at: datetime
    ended_at: datetime | None
    final_intent_profile: dict | None
    turn_count: int
    inferred_scenario: str | None  # For free_form

class ConversationTurn(BaseModel):
    session_id: str
    turn_number: int
    timestamp: datetime
    user_message: str
    assistant_response: str
    response_time_ms: int
    tool_calls: list[dict]
    intent_profile_snapshot: dict
```

### TypeScript (Frontend)

```typescript
interface Scenario {
  id: string;
  name: string;
  icon: string;
  shortDesc: string;
  persona: string | null;
}
```

## SQLite Schema

```sql
CREATE TABLE scenarios (
    scenario_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    icon TEXT,
    short_desc TEXT,
    persona_description TEXT,
    expected_intents TEXT,  -- JSON array
    expected_life_stage TEXT,
    expected_risk_preference TEXT
);

CREATE TABLE sessions (
    session_id TEXT PRIMARY KEY,
    scenario_id TEXT NOT NULL,
    created_at TEXT NOT NULL,
    ended_at TEXT,
    final_intent_profile TEXT,  -- JSON
    turn_count INTEGER DEFAULT 0,
    inferred_scenario TEXT,
    FOREIGN KEY (scenario_id) REFERENCES scenarios(scenario_id)
);

CREATE TABLE turns (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    turn_number INTEGER NOT NULL,
    timestamp TEXT NOT NULL,
    user_message TEXT NOT NULL,
    assistant_response TEXT NOT NULL,
    response_time_ms INTEGER,
    tool_calls TEXT,  -- JSON array
    intent_profile_snapshot TEXT,  -- JSON
    FOREIGN KEY (session_id) REFERENCES sessions(session_id)
);

CREATE INDEX idx_sessions_scenario ON sessions(scenario_id);
CREATE INDEX idx_sessions_created ON sessions(created_at);
CREATE INDEX idx_turns_session ON turns(session_id);
```

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     Frontend                                     │
│  ┌──────────────────┐  ┌──────────────────────────────────────┐ │
│  │ ScenarioSelector │  │          Chat Interface              │ │
│  │  (Role Cards)    │──│  (passes scenario_id in context)     │ │
│  └──────────────────┘  └──────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                     Backend                                      │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  Router (extracts scenario_id from context)              │   │
│  └──────────────────────────────────────────────────────────┘   │
│                              │                                   │
│                              ▼                                   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  Agent.invoke()                                           │   │
│  │  ├─ ensure_session(session_id, scenario_id)              │   │
│  │  ├─ run_graph(input)                                     │   │
│  │  └─ log_turn(session_id, messages, tool_calls, profile)  │   │
│  └──────────────────────────────────────────────────────────┘   │
│                              │                                   │
│                              ▼                                   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  ConversationLogger                                       │   │
│  │  └─ SQLite (data/conversation_logs.db)                   │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

## File Structure

```
src/agent_will_smith/
├── conversation_analytics/          # New module
│   ├── __init__.py
│   ├── models.py                   # Pydantic models
│   ├── database.py                 # SQLite connection & schema
│   ├── logger.py                   # ConversationLogger class
│   └── scenarios.py                # Predefined scenarios

data/
└── conversation_logs.db            # SQLite file (auto-created)

frontend/
├── lib/
│   ├── scenarios.ts                # Scenario definitions
│   └── scenario-context.tsx        # Scenario state context
└── components/assistant-ui/
    └── scenario-selector.tsx       # Role cards UI
```

## API Contract

### Scenario passed via context

```typescript
// Frontend sends scenario_id in chat request context
{
  "message": "...",
  "session_id": "...",
  "context": {
    "scenario_id": "cxo_wealth"  // Added field
  }
}
```

### Scenarios endpoint (optional, for dynamic loading)

```
GET /api/v1/scenarios
Response: { scenarios: Scenario[] }
```

## Future: Evaluation (Week 2+)

- Human annotation interface
- LLM-as-Judge for fluency/relevance
- Metrics dashboard
- A/B testing support
