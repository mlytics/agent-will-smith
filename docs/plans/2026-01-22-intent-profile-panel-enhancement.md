# Intent Profile Panel Enhancement Design

**Date**: 2026-01-22
**Status**: Approved
**Goal**: 增強右側欄 Intent Profile Panel，支援完整的意圖追蹤生命週期展示

---

## Overview

為 POC 展示優化右側欄，讓使用者可以：
- **View** - 清楚看到所有捕獲的意圖
- **Track** - 時間線追蹤每個信號
- **Dig in** - 展開查看詳細資訊
- **Audit** - 驗證 LLM 判斷是否合理

---

## Part 1: Data Structure

### Backend IntentProfile Extension

```python
class FinancialGoal(BaseModel):
    """User's financial goal extracted from conversation."""
    target_age: Optional[int] = None           # 50
    target_amount: Optional[str] = None        # "2000萬"
    timeline: Optional[str] = None             # "5年"
    goal_type: Optional[str] = None            # "retirement", "wealth_growth"

class IntentProfile(BaseModel):
    # Existing fields
    life_stage: Optional[str]           # early_career, mid_career, pre_retirement, retired
    risk_preference: Optional[str]      # conservative, moderate, aggressive
    product_interests: list[str]        # ["retirement", "investment"]
    intent_score: float                 # 0.0-1.0
    signals: list[IntentSignal]         # Signal history

    # New fields
    financial_goal: Optional[FinancialGoal]    # Financial goal
    current_assets: Optional[str]              # "1000萬台幣"
    investment_experience: Optional[str]       # beginner, intermediate, experienced
```

### Frontend TypeScript Types

```typescript
interface IntentSignal {
  signal_type: "explicit" | "inferred" | "clarified";
  category: string;
  confidence: number;
  timestamp: string;
}

interface FinancialGoal {
  target_age?: number;
  target_amount?: string;
  timeline?: string;
  goal_type?: string;
}

interface IntentProfile {
  life_stage: string | null;
  risk_preference: "conservative" | "moderate" | "aggressive" | null;
  product_interests: string[];
  intent_score: number;
  signals: IntentSignal[];
  financial_goal: FinancialGoal | null;
  current_assets: string | null;
  investment_experience: string | null;
}
```

---

## Part 2: intent_capture_tool Extension

### New Tool Parameters

```python
@tool("intent_capture")
def intent_capture_tool(
    # Required - Signal classification
    category: str,           # retirement, investment, risk_assessment, etc.
    signal_type: str,        # explicit, inferred, clarified
    confidence: float,       # 0.0-1.0

    # Optional - User Profile
    life_stage: Optional[str] = None,           # early_career, mid_career, pre_retirement, retired
    risk_preference: Optional[str] = None,      # conservative, moderate, aggressive
    investment_experience: Optional[str] = None, # beginner, intermediate, experienced

    # Optional - Financial Goal
    target_age: Optional[int] = None,           # Target retirement age
    target_amount: Optional[str] = None,        # Target amount "2000萬"
    timeline: Optional[str] = None,             # Timeline "5年"
    goal_type: Optional[str] = None,            # retirement, wealth_growth, education

    # Optional - Assets
    current_assets: Optional[str] = None,       # "1000萬台幣"
) -> dict:
```

### Prompt Guidelines for LLM

```
### intent_capture tool Usage Guide

**Required fields** - Always fill:
- category: Intent category
- signal_type: explicit(stated)/inferred(implied)/clarified(after follow-up)
- confidence: 0.0-1.0

**Optional fields** - Fill when user mentions:
- life_stage: When user mentions age/career stage (e.g., "快退休了"→pre_retirement)
- risk_preference: When user expresses risk attitude (e.g., "100%增長"→aggressive)
- target_age: When user mentions target retirement age (e.g., "50歲退休"→50)
- target_amount: When user mentions target amount (e.g., "存到兩千萬")
- timeline: When user mentions time range (e.g., "五年內")
- current_assets: When user mentions current assets (e.g., "目前有一千萬")
- investment_experience: When user mentions investment experience
```

---

## Part 3: UI Design

### Component Structure

```
IntentProfilePanel/
├── IntentClarity        # Intent clarity score (existing, keep)
├── UserProfile          # User profile card (new)
├── FinancialGoalCard    # Financial goal card (new)
├── InterestsSection     # Interest tags (existing, keep)
├── SignalHistory        # Signal history (new, collapsible)
└── SessionStats         # Session stats (new)
```

### Visual Layout

```
┌─────────────────────────────────┐
│  🎯 Your Profile                │
│  Insights from our conversation │
├─────────────────────────────────┤
│  INTENT CLARITY           90%  │
│  ████████████████████░░░░      │
│  Ready for recommendations      │
├─────────────────────────────────┤
│  👤 USER PROFILE                │
│  ┌─────────────────────────────┐│
│  │ Life Stage    Pre-retirement││
│  │ Risk          Aggressive    ││
│  │ Experience    Intermediate  ││
│  │ Assets        NT$ 1,000萬   ││
│  └─────────────────────────────┘│
├─────────────────────────────────┤
│  🎯 FINANCIAL GOAL              │
│  ┌─────────────────────────────┐│
│  │ 🎂 Target Age    50歲       ││
│  │ 💰 Target        NT$ 2,000萬││
│  │ ⏱️ Timeline      5年內      ││
│  └─────────────────────────────┘│
├─────────────────────────────────┤
│  💡 INTERESTS                   │
│  [Retirement] [Investment]      │
│  [Risk Assessment]              │
├─────────────────────────────────┤
│  📜 SIGNAL HISTORY        [▼]  │
│  ┌─────────────────────────────┐│
│  │ 15:53  retirement           ││
│  │        explicit · 90%       ││
│  ├─────────────────────────────┤│
│  │ 15:55  investment           ││
│  │        inferred · 70%       ││
│  └─────────────────────────────┘│
├─────────────────────────────────┤
│  Turns: 5  ·  Signals: 3       │
└─────────────────────────────────┘
```

### Interaction Behavior

| Section | Behavior |
|---------|----------|
| Intent Clarity | Static display, color changes with score |
| User Profile | Only show fields with values |
| Financial Goal | Show section only when any value exists |
| Interests | Tags clickable (for future filtering) |
| Signal History | Collapsed by default, click to expand, max 10 recent |
| Session Stats | Static display at bottom |

---

## Part 4: Implementation Tasks

### Backend Tasks

| # | Task | File |
|---|------|------|
| B1 | Add `FinancialGoal` model | `state.py` |
| B2 | Extend `IntentProfile` with new fields | `state.py` |
| B3 | Extend `intent_capture_tool` parameters | `intent_capture_tool.py` |
| B4 | Update `tool_execution_node` for new fields | `tool_execution_node.py` |
| B5 | Update `response_node` to pass full signals | `response_node.py` |
| B6 | Update API DTO to sync new fields | `dto.py` |
| B7 | Update system prompt for LLM guidance | `test.intent_chat_system.txt` |

### Frontend Tasks

| # | Task | File |
|---|------|------|
| F1 | Update TypeScript type definitions | `types.ts` |
| F2 | Update context for new fields | `intent-profile-context.tsx` |
| F3 | Create `UserProfileCard` component | `user-profile-card.tsx` |
| F4 | Create `FinancialGoalCard` component | `financial-goal-card.tsx` |
| F5 | Create `SignalHistory` component (collapsible) | `signal-history.tsx` |
| F6 | Create `SessionStats` component | `session-stats.tsx` |
| F7 | Refactor `IntentProfilePanel` to integrate all | `intent-profile-panel.tsx` |

### Dependency Order

```
B1 → B2 → B3 → B4 → B5 → B6 → B7 (Backend serial)
                ↓
F1 → F2 → F3/F4/F5/F6 (Parallel) → F7 (Frontend)
```

---

## Decision Log

| Question | Decision | Reason |
|----------|----------|--------|
| Signal History display | Compact List (collapsible) | Space efficient, can expand for details |
| User Profile fields | Full version with assets/experience | Easy to extend intent_capture_tool |
| Session Stats | Simple (turns + signals only) | Frontend calculated, keep simple |
