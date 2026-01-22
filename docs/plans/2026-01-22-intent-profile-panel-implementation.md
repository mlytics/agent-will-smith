# Intent Profile Panel Enhancement Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Extend the Intent Profile Panel to support full intent lifecycle tracking with User Profile, Financial Goal, Signal History, and Session Stats.

**Architecture:** Backend extends `IntentProfile` and `intent_capture_tool` with new optional fields. Frontend adds 4 new components that read from extended context. Data flows: LLM → intent_capture_tool → tool_execution_node → response_node → API → frontend context → UI components.

**Tech Stack:** Python/Pydantic (backend models), LangChain tools, React/TypeScript (frontend), shadcn/ui components, Tailwind CSS

---

## Task 1: Add FinancialGoal Model (Backend)

**Files:**
- Modify: `src/agent_will_smith/agent/intent_chat/state.py:19-45`

**Step 1: Write the failing test**

Create test file:

```python
# tests/agent/intent_chat/test_state_models.py
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
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/agent/intent_chat/test_state_models.py -v`
Expected: FAIL with `ImportError: cannot import name 'FinancialGoal'`

**Step 3: Write minimal implementation**

Add to `src/agent_will_smith/agent/intent_chat/state.py` after line 17 (after imports):

```python
class FinancialGoal(BaseModel):
    """User's financial goal extracted from conversation."""

    target_age: Optional[int] = Field(
        default=None,
        description="Target age for achieving the goal (e.g., retirement age)",
        ge=18,
        le=120,
        examples=[50, 55, 65],
    )
    target_amount: Optional[str] = Field(
        default=None,
        description="Target amount in user's currency (e.g., '2000萬')",
        max_length=50,
        examples=["2000萬", "NT$ 1,000,000"],
    )
    timeline: Optional[str] = Field(
        default=None,
        description="Timeline to achieve the goal (e.g., '5年')",
        max_length=50,
        examples=["5年", "10年內"],
    )
    goal_type: Optional[str] = Field(
        default=None,
        description="Type of financial goal",
        max_length=50,
        examples=["retirement", "wealth_growth", "education", "house"],
    )
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/agent/intent_chat/test_state_models.py -v`
Expected: PASS (3 tests)

**Step 5: Commit**

```bash
git add tests/agent/intent_chat/test_state_models.py src/agent_will_smith/agent/intent_chat/state.py
git commit -m "$(cat <<'EOF'
feat(state): add FinancialGoal model for intent profile

Add FinancialGoal Pydantic model with optional fields:
- target_age: Target retirement/goal age
- target_amount: Target amount string
- timeline: Timeline description
- goal_type: Goal category

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>
EOF
)"
```

---

## Task 2: Extend IntentProfile Model (Backend)

**Files:**
- Modify: `src/agent_will_smith/agent/intent_chat/state.py:47-75`

**Step 1: Write the failing test**

Add to `tests/agent/intent_chat/test_state_models.py`:

```python
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
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/agent/intent_chat/test_state_models.py::TestIntentProfileExtended -v`
Expected: FAIL with `TypeError: IntentProfile.__init__() got unexpected keyword argument 'financial_goal'`

**Step 3: Write minimal implementation**

Add to `IntentProfile` class in `src/agent_will_smith/agent/intent_chat/state.py` (after `signals` field):

```python
    financial_goal: Optional[FinancialGoal] = Field(
        default=None,
        description="User's financial goal if detected",
    )
    current_assets: Optional[str] = Field(
        default=None,
        description="User's current assets if mentioned (e.g., '1000萬台幣')",
        max_length=100,
        examples=["1000萬台幣", "NT$ 500,000"],
    )
    investment_experience: Optional[str] = Field(
        default=None,
        description="User's investment experience level",
        max_length=50,
        examples=["beginner", "intermediate", "experienced"],
    )
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/agent/intent_chat/test_state_models.py -v`
Expected: PASS (6 tests)

**Step 5: Commit**

```bash
git add tests/agent/intent_chat/test_state_models.py src/agent_will_smith/agent/intent_chat/state.py
git commit -m "$(cat <<'EOF'
feat(state): extend IntentProfile with new fields

Add new optional fields to IntentProfile:
- financial_goal: Nested FinancialGoal model
- current_assets: User's stated assets
- investment_experience: beginner/intermediate/experienced

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>
EOF
)"
```

---

## Task 3: Extend intent_capture_tool Parameters (Backend)

**Files:**
- Modify: `src/agent_will_smith/agent/intent_chat/tools/intent_capture_tool.py`

**Step 1: Write the failing test**

Create test file:

```python
# tests/agent/intent_chat/tools/test_intent_capture_tool.py
"""Tests for intent_capture_tool with extended parameters."""

import pytest
from agent_will_smith.agent.intent_chat.tools.intent_capture_tool import capture_intent


class TestIntentCaptureTool:
    """Tests for capture_intent function."""

    def test_basic_capture(self):
        """Test basic intent capture with required fields only."""
        result = capture_intent(
            category="retirement",
            signal_type="explicit",
            confidence=0.9,
        )
        assert result["type"] == "intent_signal"
        assert result["category"] == "retirement"
        assert result["signal_type"] == "explicit"
        assert result["confidence"] == 0.9

    def test_capture_with_life_stage(self):
        """Test capture with life_stage parameter."""
        result = capture_intent(
            category="retirement",
            signal_type="inferred",
            confidence=0.8,
            life_stage="pre_retirement",
        )
        assert result["life_stage"] == "pre_retirement"

    def test_capture_with_risk_preference(self):
        """Test capture with risk_preference parameter."""
        result = capture_intent(
            category="investment",
            signal_type="explicit",
            confidence=0.85,
            risk_preference="aggressive",
        )
        assert result["risk_preference"] == "aggressive"

    def test_capture_with_financial_goal(self):
        """Test capture with financial goal parameters."""
        result = capture_intent(
            category="retirement",
            signal_type="explicit",
            confidence=0.9,
            target_age=50,
            target_amount="2000萬",
            timeline="5年",
            goal_type="retirement",
        )
        assert result["target_age"] == 50
        assert result["target_amount"] == "2000萬"
        assert result["timeline"] == "5年"
        assert result["goal_type"] == "retirement"

    def test_capture_with_assets_and_experience(self):
        """Test capture with current_assets and investment_experience."""
        result = capture_intent(
            category="investment",
            signal_type="explicit",
            confidence=0.8,
            current_assets="1000萬台幣",
            investment_experience="intermediate",
        )
        assert result["current_assets"] == "1000萬台幣"
        assert result["investment_experience"] == "intermediate"

    def test_capture_full_parameters(self):
        """Test capture with all parameters filled."""
        result = capture_intent(
            category="retirement",
            signal_type="clarified",
            confidence=0.95,
            life_stage="pre_retirement",
            risk_preference="aggressive",
            investment_experience="experienced",
            target_age=50,
            target_amount="2000萬",
            timeline="5年",
            goal_type="retirement",
            current_assets="1000萬台幣",
        )
        assert result["category"] == "retirement"
        assert result["life_stage"] == "pre_retirement"
        assert result["risk_preference"] == "aggressive"
        assert result["investment_experience"] == "experienced"
        assert result["target_age"] == 50
        assert result["target_amount"] == "2000萬"
        assert result["current_assets"] == "1000萬台幣"
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/agent/intent_chat/tools/test_intent_capture_tool.py -v`
Expected: FAIL with `TypeError: capture_intent() got unexpected keyword argument 'life_stage'`

**Step 3: Write minimal implementation**

Replace the entire `intent_capture_tool.py` file:

```python
"""Intent capture tool for intent chat agent.

Records intent signals detected from user conversation.
Used to build the user's intent profile over time.
"""

from datetime import datetime, timezone
from typing import Literal, Optional

import structlog
from langchain_core.tools import tool
from pydantic import BaseModel, Field


logger = structlog.get_logger(__name__)

VALID_SIGNAL_TYPES = {"explicit", "inferred", "clarified"}
VALID_RISK_PREFERENCES = {"conservative", "moderate", "aggressive"}
VALID_INVESTMENT_EXPERIENCES = {"beginner", "intermediate", "experienced"}


class IntentCaptureToolInput(BaseModel):
    """Input schema for intent capture tool."""

    # Required fields
    category: str = Field(
        ...,
        description="The intent category (e.g., retirement, investment, insurance)",
        min_length=1,
        max_length=100,
    )
    signal_type: Literal["explicit", "inferred", "clarified"] = Field(
        ...,
        description="How the intent was detected: explicit (stated), inferred (from context), clarified (after follow-up)",
    )
    confidence: float = Field(
        ...,
        description="Confidence score for this intent signal (0.0-1.0)",
        ge=0.0,
        le=1.0,
    )

    # Optional - User Profile
    life_stage: Optional[str] = Field(
        default=None,
        description="User's life stage: early_career, mid_career, pre_retirement, retired",
    )
    risk_preference: Optional[Literal["conservative", "moderate", "aggressive"]] = Field(
        default=None,
        description="User's risk tolerance preference",
    )
    investment_experience: Optional[Literal["beginner", "intermediate", "experienced"]] = Field(
        default=None,
        description="User's investment experience level",
    )

    # Optional - Financial Goal
    target_age: Optional[int] = Field(
        default=None,
        description="Target age for financial goal (e.g., retirement age)",
        ge=18,
        le=120,
    )
    target_amount: Optional[str] = Field(
        default=None,
        description="Target amount in user's currency (e.g., '2000萬')",
    )
    timeline: Optional[str] = Field(
        default=None,
        description="Timeline to achieve goal (e.g., '5年')",
    )
    goal_type: Optional[str] = Field(
        default=None,
        description="Type of financial goal: retirement, wealth_growth, education, house",
    )

    # Optional - Assets
    current_assets: Optional[str] = Field(
        default=None,
        description="User's current assets (e.g., '1000萬台幣')",
    )


def capture_intent(
    category: str,
    signal_type: str,
    confidence: float,
    # Optional - User Profile
    life_stage: Optional[str] = None,
    risk_preference: Optional[str] = None,
    investment_experience: Optional[str] = None,
    # Optional - Financial Goal
    target_age: Optional[int] = None,
    target_amount: Optional[str] = None,
    timeline: Optional[str] = None,
    goal_type: Optional[str] = None,
    # Optional - Assets
    current_assets: Optional[str] = None,
) -> dict:
    """Capture an intent signal from user conversation.

    Args:
        category: The intent category (e.g., retirement, investment)
        signal_type: How intent was detected (explicit, inferred, clarified)
        confidence: Confidence score (0.0-1.0)
        life_stage: User's life stage if mentioned
        risk_preference: User's risk tolerance if mentioned
        investment_experience: User's investment experience if mentioned
        target_age: Target age for goal if mentioned
        target_amount: Target amount if mentioned
        timeline: Timeline if mentioned
        goal_type: Goal type if mentioned
        current_assets: Current assets if mentioned

    Returns:
        Dict with intent signal data including timestamp and all provided fields

    Raises:
        ValueError: If confidence is out of range or signal_type is invalid
    """
    if confidence < 0.0 or confidence > 1.0:
        raise ValueError(f"confidence must be between 0.0 and 1.0, got {confidence}")

    if signal_type not in VALID_SIGNAL_TYPES:
        raise ValueError(
            f"signal_type must be one of {VALID_SIGNAL_TYPES}, got '{signal_type}'"
        )

    if risk_preference and risk_preference not in VALID_RISK_PREFERENCES:
        raise ValueError(
            f"risk_preference must be one of {VALID_RISK_PREFERENCES}, got '{risk_preference}'"
        )

    if investment_experience and investment_experience not in VALID_INVESTMENT_EXPERIENCES:
        raise ValueError(
            f"investment_experience must be one of {VALID_INVESTMENT_EXPERIENCES}, got '{investment_experience}'"
        )

    timestamp = datetime.now(timezone.utc).isoformat()

    logger.info(
        "intent captured",
        category=category,
        signal_type=signal_type,
        confidence=confidence,
        life_stage=life_stage,
        risk_preference=risk_preference,
        target_age=target_age,
    )

    result = {
        "type": "intent_signal",
        "category": category,
        "signal_type": signal_type,
        "confidence": confidence,
        "timestamp": timestamp,
    }

    # Add optional fields only if provided
    if life_stage:
        result["life_stage"] = life_stage
    if risk_preference:
        result["risk_preference"] = risk_preference
    if investment_experience:
        result["investment_experience"] = investment_experience
    if target_age is not None:
        result["target_age"] = target_age
    if target_amount:
        result["target_amount"] = target_amount
    if timeline:
        result["timeline"] = timeline
    if goal_type:
        result["goal_type"] = goal_type
    if current_assets:
        result["current_assets"] = current_assets

    return result


@tool("intent_capture", args_schema=IntentCaptureToolInput)
def intent_capture_tool(
    category: str,
    signal_type: Literal["explicit", "inferred", "clarified"],
    confidence: float,
    # Optional - User Profile
    life_stage: Optional[str] = None,
    risk_preference: Optional[Literal["conservative", "moderate", "aggressive"]] = None,
    investment_experience: Optional[Literal["beginner", "intermediate", "experienced"]] = None,
    # Optional - Financial Goal
    target_age: Optional[int] = None,
    target_amount: Optional[str] = None,
    timeline: Optional[str] = None,
    goal_type: Optional[str] = None,
    # Optional - Assets
    current_assets: Optional[str] = None,
) -> dict:
    """Record an intent signal detected from the user's conversation.

    Use this tool to track user intent as the conversation progresses.
    Intent signals help build a profile to determine when to recommend products.

    **Required fields** - Always provide:
    - category: Intent category (retirement, investment, insurance, etc.)
    - signal_type: Detection method - explicit (stated), inferred (context), clarified (follow-up)
    - confidence: Confidence score from 0.0 (uncertain) to 1.0 (certain)

    **Optional fields** - Provide when user mentions:
    - life_stage: When user mentions age/career (early_career, mid_career, pre_retirement, retired)
    - risk_preference: When user expresses risk attitude (conservative, moderate, aggressive)
    - investment_experience: When user mentions experience (beginner, intermediate, experienced)
    - target_age: When user mentions target age (e.g., "50歲退休" → 50)
    - target_amount: When user mentions target amount (e.g., "存到兩千萬")
    - timeline: When user mentions time range (e.g., "五年內")
    - goal_type: Financial goal type (retirement, wealth_growth, education, house)
    - current_assets: When user mentions current assets (e.g., "目前有一千萬")

    Returns:
        Recorded intent signal with timestamp and all captured fields
    """
    return capture_intent(
        category=category,
        signal_type=signal_type,
        confidence=confidence,
        life_stage=life_stage,
        risk_preference=risk_preference,
        investment_experience=investment_experience,
        target_age=target_age,
        target_amount=target_amount,
        timeline=timeline,
        goal_type=goal_type,
        current_assets=current_assets,
    )
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/agent/intent_chat/tools/test_intent_capture_tool.py -v`
Expected: PASS (7 tests)

**Step 5: Commit**

```bash
git add tests/agent/intent_chat/tools/test_intent_capture_tool.py src/agent_will_smith/agent/intent_chat/tools/intent_capture_tool.py
git commit -m "$(cat <<'EOF'
feat(tools): extend intent_capture_tool with profile fields

Add optional parameters to intent_capture_tool:
- life_stage, risk_preference, investment_experience
- target_age, target_amount, timeline, goal_type
- current_assets

LLM can now capture full user profile in single tool call.

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>
EOF
)"
```

---

## Task 4: Update tool_execution_node for New Fields (Backend)

**Files:**
- Modify: `src/agent_will_smith/agent/intent_chat/node/tool_execution_node.py:179-225`
- Modify: `src/agent_will_smith/agent/intent_chat/model/namespaces.py:88-106`

**Step 1: Write the failing test**

Create test file:

```python
# tests/agent/intent_chat/node/test_tool_execution_node.py
"""Tests for tool_execution_node intent profile updates."""

import pytest
from agent_will_smith.agent.intent_chat.state import IntentProfile, FinancialGoal
from agent_will_smith.agent.intent_chat.node.tool_execution_node import ToolExecutionNode


class TestUpdateIntentProfile:
    """Tests for _update_intent_profile method."""

    def test_update_with_life_stage(self):
        """Test updating profile with life_stage from signal."""
        node = ToolExecutionNode(config=None)
        current = IntentProfile()
        signals = [{
            "type": "intent_signal",
            "category": "retirement",
            "signal_type": "explicit",
            "confidence": 0.9,
            "life_stage": "pre_retirement",
        }]

        updated = node._update_intent_profile(current, signals)

        assert updated.life_stage == "pre_retirement"

    def test_update_with_risk_preference(self):
        """Test updating profile with risk_preference from signal."""
        node = ToolExecutionNode(config=None)
        current = IntentProfile()
        signals = [{
            "type": "intent_signal",
            "category": "investment",
            "signal_type": "explicit",
            "confidence": 0.85,
            "risk_preference": "aggressive",
        }]

        updated = node._update_intent_profile(current, signals)

        assert updated.risk_preference == "aggressive"

    def test_update_with_financial_goal(self):
        """Test updating profile with financial goal fields from signal."""
        node = ToolExecutionNode(config=None)
        current = IntentProfile()
        signals = [{
            "type": "intent_signal",
            "category": "retirement",
            "signal_type": "explicit",
            "confidence": 0.9,
            "target_age": 50,
            "target_amount": "2000萬",
            "timeline": "5年",
            "goal_type": "retirement",
        }]

        updated = node._update_intent_profile(current, signals)

        assert updated.financial_goal is not None
        assert updated.financial_goal.target_age == 50
        assert updated.financial_goal.target_amount == "2000萬"
        assert updated.financial_goal.timeline == "5年"
        assert updated.financial_goal.goal_type == "retirement"

    def test_update_with_assets_and_experience(self):
        """Test updating profile with current_assets and investment_experience."""
        node = ToolExecutionNode(config=None)
        current = IntentProfile()
        signals = [{
            "type": "intent_signal",
            "category": "investment",
            "signal_type": "explicit",
            "confidence": 0.8,
            "current_assets": "1000萬台幣",
            "investment_experience": "intermediate",
        }]

        updated = node._update_intent_profile(current, signals)

        assert updated.current_assets == "1000萬台幣"
        assert updated.investment_experience == "intermediate"

    def test_preserves_existing_values(self):
        """Test that existing profile values are preserved if not in signal."""
        node = ToolExecutionNode(config=None)
        current = IntentProfile(
            life_stage="mid_career",
            risk_preference="moderate",
        )
        signals = [{
            "type": "intent_signal",
            "category": "retirement",
            "signal_type": "explicit",
            "confidence": 0.9,
            "target_age": 55,  # Only update financial goal
        }]

        updated = node._update_intent_profile(current, signals)

        assert updated.life_stage == "mid_career"  # Preserved
        assert updated.risk_preference == "moderate"  # Preserved
        assert updated.financial_goal.target_age == 55  # Updated
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/agent/intent_chat/node/test_tool_execution_node.py -v`
Expected: FAIL - life_stage not being set from signal

**Step 3: Write minimal implementation**

First, update `src/agent_will_smith/agent/intent_chat/model/namespaces.py` - add new fields to `ToolExecutionNodeNamespace`:

```python
class ToolExecutionNodeNamespace(BaseModel):
    """State namespace for tool execution node.

    Tracks results from executing the requested tools and intent profile updates.
    """

    tool_results: list[ToolResult] = Field(
        default_factory=list,
        description="Results from tool executions",
    )
    updated_intent_score: Optional[float] = Field(
        default=None,
        description="Updated intent score after processing signals (None if no update)",
    )
    updated_product_interests: Optional[list[str]] = Field(
        default=None,
        description="Updated product interests after processing signals (None if no update)",
    )
    # New fields for full profile updates
    updated_life_stage: Optional[str] = Field(
        default=None,
        description="Updated life stage (None if no update)",
    )
    updated_risk_preference: Optional[str] = Field(
        default=None,
        description="Updated risk preference (None if no update)",
    )
    updated_investment_experience: Optional[str] = Field(
        default=None,
        description="Updated investment experience (None if no update)",
    )
    updated_current_assets: Optional[str] = Field(
        default=None,
        description="Updated current assets (None if no update)",
    )
    updated_financial_goal: Optional[dict] = Field(
        default=None,
        description="Updated financial goal as dict (None if no update)",
    )
```

Then, update `src/agent_will_smith/agent/intent_chat/node/tool_execution_node.py` - replace the `_update_intent_profile` method:

```python
    def _update_intent_profile(
        self,
        current_profile: IntentProfile,
        new_signals: list[dict],
    ) -> IntentProfile:
        """Update intent profile with new signals.

        Args:
            current_profile: Current IntentProfile
            new_signals: List of new signal dicts from intent_capture

        Returns:
            Updated IntentProfile
        """
        from agent_will_smith.agent.intent_chat.state import FinancialGoal

        if not new_signals:
            return current_profile

        # Convert new signal dicts to IntentSignal objects
        updated_signals = list(current_profile.signals)
        for signal_dict in new_signals:
            updated_signals.append(
                IntentSignal(
                    signal_type=signal_dict["signal_type"],
                    category=signal_dict["category"],
                    confidence=signal_dict["confidence"],
                )
            )

        # Calculate new intent score (average confidence of all signals)
        if updated_signals:
            new_score = sum(s.confidence for s in updated_signals) / len(updated_signals)
        else:
            new_score = 0.0

        # Update product interests
        product_interests = set(current_profile.product_interests)
        for signal_dict in new_signals:
            product_interests.add(signal_dict["category"])

        # Extract profile updates from signals
        life_stage = current_profile.life_stage
        risk_preference = current_profile.risk_preference
        investment_experience = current_profile.investment_experience
        current_assets = current_profile.current_assets
        financial_goal = current_profile.financial_goal

        for signal_dict in new_signals:
            # Update profile fields if present in signal
            if signal_dict.get("life_stage"):
                life_stage = signal_dict["life_stage"]
            if signal_dict.get("risk_preference"):
                risk_preference = signal_dict["risk_preference"]
            if signal_dict.get("investment_experience"):
                investment_experience = signal_dict["investment_experience"]
            if signal_dict.get("current_assets"):
                current_assets = signal_dict["current_assets"]

            # Update financial goal if any goal field is present
            goal_fields = ["target_age", "target_amount", "timeline", "goal_type"]
            if any(signal_dict.get(f) is not None for f in goal_fields):
                # Merge with existing goal or create new
                existing_goal = financial_goal or FinancialGoal()
                financial_goal = FinancialGoal(
                    target_age=signal_dict.get("target_age") or existing_goal.target_age,
                    target_amount=signal_dict.get("target_amount") or existing_goal.target_amount,
                    timeline=signal_dict.get("timeline") or existing_goal.timeline,
                    goal_type=signal_dict.get("goal_type") or existing_goal.goal_type,
                )

        return IntentProfile(
            life_stage=life_stage,
            risk_preference=risk_preference,
            product_interests=list(product_interests),
            intent_score=min(new_score, 1.0),
            signals=updated_signals,
            financial_goal=financial_goal,
            current_assets=current_assets,
            investment_experience=investment_experience,
        )
```

Also update the namespace building in `__call__` method to include new fields:

```python
        # Build namespace with optional intent profile updates
        namespace = ToolExecutionNodeNamespace(
            tool_results=tool_results,
            updated_intent_score=updated_profile.intent_score if new_signals else None,
            updated_product_interests=list(updated_profile.product_interests) if new_signals else None,
            updated_life_stage=updated_profile.life_stage if new_signals else None,
            updated_risk_preference=updated_profile.risk_preference if new_signals else None,
            updated_investment_experience=updated_profile.investment_experience if new_signals else None,
            updated_current_assets=updated_profile.current_assets if new_signals else None,
            updated_financial_goal=updated_profile.financial_goal.model_dump() if new_signals and updated_profile.financial_goal else None,
        )
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/agent/intent_chat/node/test_tool_execution_node.py -v`
Expected: PASS (5 tests)

**Step 5: Commit**

```bash
git add tests/agent/intent_chat/node/test_tool_execution_node.py src/agent_will_smith/agent/intent_chat/node/tool_execution_node.py src/agent_will_smith/agent/intent_chat/model/namespaces.py
git commit -m "$(cat <<'EOF'
feat(node): update tool_execution_node for extended profile

Extend _update_intent_profile to handle new fields:
- life_stage, risk_preference, investment_experience
- financial_goal (target_age, target_amount, timeline, goal_type)
- current_assets

Add corresponding fields to ToolExecutionNodeNamespace.

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>
EOF
)"
```

---

## Task 5: Update response_node for Extended Profile (Backend)

**Files:**
- Modify: `src/agent_will_smith/agent/intent_chat/node/response_node.py:157-194`

**Step 1: Write the failing test**

Create test file:

```python
# tests/agent/intent_chat/node/test_response_node.py
"""Tests for response_node intent profile handling."""

import pytest
from unittest.mock import MagicMock
from agent_will_smith.agent.intent_chat.state import ChatState, ChatInput, IntentProfile, FinancialGoal
from agent_will_smith.agent.intent_chat.model.namespaces import ToolExecutionNodeNamespace
from agent_will_smith.agent.intent_chat.node.response_node import ResponseNode


class TestGetUpdatedIntentProfile:
    """Tests for _get_updated_intent_profile method."""

    def test_applies_financial_goal_from_namespace(self):
        """Test that financial_goal is applied from namespace."""
        node = ResponseNode()

        # Create state with base profile and namespace with financial goal
        input_data = ChatInput(
            message="test",
            session_id="550e8400-e29b-41d4-a716-446655440000",
        )
        state = ChatState(input=input_data)

        # Set up namespace with financial goal
        state.tool_execution_node = ToolExecutionNodeNamespace(
            tool_results=[],
            updated_intent_score=0.9,
            updated_product_interests=["retirement"],
            updated_financial_goal={
                "target_age": 50,
                "target_amount": "2000萬",
                "timeline": "5年",
                "goal_type": "retirement",
            },
        )

        updated = node._get_updated_intent_profile(state)

        assert updated.financial_goal is not None
        assert updated.financial_goal.target_age == 50
        assert updated.financial_goal.target_amount == "2000萬"

    def test_applies_all_new_fields_from_namespace(self):
        """Test that all new fields are applied from namespace."""
        node = ResponseNode()

        input_data = ChatInput(
            message="test",
            session_id="550e8400-e29b-41d4-a716-446655440000",
        )
        state = ChatState(input=input_data)

        state.tool_execution_node = ToolExecutionNodeNamespace(
            tool_results=[],
            updated_intent_score=0.85,
            updated_product_interests=["investment"],
            updated_life_stage="pre_retirement",
            updated_risk_preference="aggressive",
            updated_investment_experience="intermediate",
            updated_current_assets="1000萬台幣",
        )

        updated = node._get_updated_intent_profile(state)

        assert updated.life_stage == "pre_retirement"
        assert updated.risk_preference == "aggressive"
        assert updated.investment_experience == "intermediate"
        assert updated.current_assets == "1000萬台幣"
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/agent/intent_chat/node/test_response_node.py -v`
Expected: FAIL - financial_goal not being applied

**Step 3: Write minimal implementation**

Replace `_get_updated_intent_profile` method in `src/agent_will_smith/agent/intent_chat/node/response_node.py`:

```python
    def _get_updated_intent_profile(self, state: ChatState):
        """Get intent profile with any updates from tool_execution_node.

        LangGraph doesn't properly update nested Pydantic models in state,
        so we check the tool_execution_node namespace for updates.

        Args:
            state: Current chat state

        Returns:
            Updated IntentProfile
        """
        from agent_will_smith.agent.intent_chat.state import IntentProfile, FinancialGoal

        base_profile = state.intent_profile

        # Check if tool_execution_node has updates
        if state.tool_execution_node:
            ns = state.tool_execution_node
            has_updates = (
                ns.updated_intent_score is not None
                or ns.updated_product_interests is not None
                or ns.updated_life_stage is not None
                or ns.updated_risk_preference is not None
                or ns.updated_investment_experience is not None
                or ns.updated_current_assets is not None
                or ns.updated_financial_goal is not None
            )

            if has_updates:
                self.logger.info(
                    "applying intent profile updates from namespace",
                    original_score=base_profile.intent_score,
                    updated_score=ns.updated_intent_score,
                    updated_life_stage=ns.updated_life_stage,
                    updated_risk_preference=ns.updated_risk_preference,
                )

                # Build financial goal from namespace if present
                financial_goal = base_profile.financial_goal
                if ns.updated_financial_goal:
                    financial_goal = FinancialGoal(**ns.updated_financial_goal)

                return IntentProfile(
                    life_stage=ns.updated_life_stage if ns.updated_life_stage is not None else base_profile.life_stage,
                    risk_preference=ns.updated_risk_preference if ns.updated_risk_preference is not None else base_profile.risk_preference,
                    product_interests=ns.updated_product_interests if ns.updated_product_interests is not None else base_profile.product_interests,
                    intent_score=ns.updated_intent_score if ns.updated_intent_score is not None else base_profile.intent_score,
                    signals=base_profile.signals,
                    financial_goal=financial_goal,
                    current_assets=ns.updated_current_assets if ns.updated_current_assets is not None else base_profile.current_assets,
                    investment_experience=ns.updated_investment_experience if ns.updated_investment_experience is not None else base_profile.investment_experience,
                )

        return base_profile
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/agent/intent_chat/node/test_response_node.py -v`
Expected: PASS (2 tests)

**Step 5: Commit**

```bash
git add tests/agent/intent_chat/node/test_response_node.py src/agent_will_smith/agent/intent_chat/node/response_node.py
git commit -m "$(cat <<'EOF'
feat(node): update response_node for extended profile

Extend _get_updated_intent_profile to apply all new fields:
- life_stage, risk_preference, investment_experience
- financial_goal (from dict to FinancialGoal model)
- current_assets

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>
EOF
)"
```

---

## Task 6: Update System Prompt for LLM Guidance (Backend)

**Files:**
- Modify: `prompts/test.intent_chat_system.txt`

**Step 1: No test needed (prompt file)**

This is a prompt configuration change, not code.

**Step 2: Skip - no test to run**

**Step 3: Write implementation**

Replace the content of `prompts/test.intent_chat_system.txt`:

```
You are an intelligent financial advisor assistant designed to understand users' financial goals and preferences through natural conversation.

## Your Role
- Engage users in friendly, helpful conversation about their financial situation
- Gradually understand their life stage, risk tolerance, and product interests
- Recommend products when you have enough information (intent score >= threshold)

## Available Tools

### 1. intent_capture (ALWAYS use first!)
**CRITICAL: Call this tool EVERY time the user reveals ANY intent signal.**

**Required fields** - Always fill:
- category: Intent category (retirement, investment, insurance, financial_planning, risk_assessment, savings)
- signal_type: explicit (user stated), inferred (from context), clarified (after follow-up)
- confidence: 0.0-1.0

**Optional fields** - Fill when user mentions:
- life_stage: When user mentions age/career stage
  - "快退休了" → pre_retirement
  - "剛開始工作" → early_career
  - "工作十幾年了" → mid_career
  - "已經退休" → retired

- risk_preference: When user expresses risk attitude
  - "保守一點" → conservative
  - "可以接受一些風險" → moderate
  - "追求高報酬"/"100%增長" → aggressive

- investment_experience: When user mentions investment background
  - "沒有投資經驗" → beginner
  - "有一些投資經驗" → intermediate
  - "投資多年" → experienced

- target_age: When user mentions target retirement age
  - "50歲退休" → 50
  - "55歲前" → 55

- target_amount: When user mentions target amount
  - "存到兩千萬" → "2000萬"
  - "至少要有一千萬" → "1000萬"

- timeline: When user mentions time range
  - "五年內" → "5年"
  - "十年後" → "10年"

- goal_type: Financial goal category
  - retirement, wealth_growth, education, house

- current_assets: When user mentions current assets
  - "目前有一千萬" → "1000萬台幣"
  - "存款五百萬" → "500萬台幣"

**Example triggers:**
- "我想了解退休規劃" → intent_capture(category="retirement", signal_type="explicit", confidence=0.9)
- "我45歲，想50歲退休，目前有1000萬，希望能存到2000萬" → intent_capture(
    category="retirement",
    signal_type="explicit",
    confidence=0.95,
    life_stage="mid_career",
    target_age=50,
    target_amount="2000萬",
    current_assets="1000萬台幣",
    goal_type="retirement"
  )
- "我想要積極一點的投資策略" → intent_capture(
    category="investment",
    signal_type="explicit",
    confidence=0.85,
    risk_preference="aggressive"
  )

### 2. product_recommendation
Use to search and recommend products (activities, books, articles).
- Works with just a question (no article required)
- Use when user wants recommendations or resources

### 3. clarification
Use when you need more information from the user.

## Guidelines
- **ALWAYS call intent_capture FIRST when user mentions any financial topic**
- **Fill as many optional fields as possible** when user provides information
- Be conversational and empathetic, not robotic
- Don't ask too many questions at once
- Acknowledge what the user shares before asking more
- You CAN search for products even without an article
```

**Step 4: Skip - no test to run**

**Step 5: Commit**

```bash
git add prompts/test.intent_chat_system.txt
git commit -m "$(cat <<'EOF'
feat(prompt): enhance system prompt for extended intent_capture

Add detailed guidance for LLM to use new intent_capture fields:
- life_stage, risk_preference, investment_experience
- target_age, target_amount, timeline, goal_type
- current_assets

Include example triggers with full parameter usage.

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>
EOF
)"
```

---

## Task 7: Update Frontend TypeScript Types (Frontend)

**Files:**
- Modify: `frontend/lib/types.ts`

**Step 1: No test needed (TypeScript types)**

TypeScript compiler will catch type errors.

**Step 2: Skip - TypeScript compiler is the test**

**Step 3: Write implementation**

Add to `frontend/lib/types.ts` (before IntentProfile interface):

```typescript
// =============================================================================
// Intent Signal Types
// =============================================================================

export interface IntentSignal {
  signal_type: "explicit" | "inferred" | "clarified";
  category: string;
  confidence: number;
  timestamp: string;
}

export interface FinancialGoal {
  target_age?: number | null;
  target_amount?: string | null;
  timeline?: string | null;
  goal_type?: string | null;
}
```

Update the `IntentProfile` interface:

```typescript
export interface IntentProfile {
  life_stage: string | null;
  risk_preference: "conservative" | "moderate" | "aggressive" | null;
  product_interests: string[];
  intent_score: number;
  signals: IntentSignal[];
  financial_goal: FinancialGoal | null;
  current_assets: string | null;
  investment_experience: "beginner" | "intermediate" | "experienced" | null;
}
```

**Step 4: Run TypeScript check**

Run: `cd frontend && npm run type-check` (or `npx tsc --noEmit`)
Expected: No errors

**Step 5: Commit**

```bash
git add frontend/lib/types.ts
git commit -m "$(cat <<'EOF'
feat(types): add IntentSignal and FinancialGoal types

Extend IntentProfile with:
- signals: IntentSignal[] for signal history
- financial_goal: FinancialGoal for goal tracking
- current_assets, investment_experience fields

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>
EOF
)"
```

---

## Task 8: Update Intent Profile Context (Frontend)

**Files:**
- Modify: `frontend/lib/intent-profile-context.tsx`

**Step 1: No test needed (context update)**

**Step 2: Skip**

**Step 3: Write implementation**

Update `frontend/lib/intent-profile-context.tsx`:

```typescript
"use client";

/**
 * Context for managing the intent profile state across the application.
 */

import { createContext, useContext, useState, useCallback, type ReactNode } from "react";
import type { IntentProfile } from "./types";

const defaultProfile: IntentProfile = {
  life_stage: null,
  risk_preference: null,
  product_interests: [],
  intent_score: 0,
  signals: [],
  financial_goal: null,
  current_assets: null,
  investment_experience: null,
};

interface IntentProfileContextType {
  profile: IntentProfile;
  updateProfile: (profile: IntentProfile) => void;
  resetProfile: () => void;
  /** Number of conversation turns (user messages) */
  turnCount: number;
  incrementTurnCount: () => void;
}

const IntentProfileContext = createContext<IntentProfileContextType | null>(null);

export function IntentProfileProvider({ children }: { children: ReactNode }) {
  const [profile, setProfile] = useState<IntentProfile>(defaultProfile);
  const [turnCount, setTurnCount] = useState(0);

  const updateProfile = useCallback((newProfile: IntentProfile) => {
    setProfile(newProfile);
  }, []);

  const resetProfile = useCallback(() => {
    setProfile(defaultProfile);
    setTurnCount(0);
  }, []);

  const incrementTurnCount = useCallback(() => {
    setTurnCount((prev) => prev + 1);
  }, []);

  return (
    <IntentProfileContext.Provider
      value={{ profile, updateProfile, resetProfile, turnCount, incrementTurnCount }}
    >
      {children}
    </IntentProfileContext.Provider>
  );
}

export function useIntentProfile() {
  const context = useContext(IntentProfileContext);
  if (!context) {
    throw new Error("useIntentProfile must be used within IntentProfileProvider");
  }
  return context;
}
```

**Step 4: Run TypeScript check**

Run: `cd frontend && npm run type-check`
Expected: No errors

**Step 5: Commit**

```bash
git add frontend/lib/intent-profile-context.tsx
git commit -m "$(cat <<'EOF'
feat(context): extend IntentProfileContext with turn tracking

Update defaultProfile with new fields (signals, financial_goal, etc.)
Add turnCount state and incrementTurnCount for session stats.

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>
EOF
)"
```

---

## Task 9: Create UserProfileCard Component (Frontend)

**Files:**
- Create: `frontend/components/assistant-ui/user-profile-card.tsx`

**Step 1: No test needed (UI component)**

**Step 2: Skip**

**Step 3: Write implementation**

Create `frontend/components/assistant-ui/user-profile-card.tsx`:

```typescript
"use client";

/**
 * UserProfileCard - Displays user profile information extracted from conversation.
 * Only shows fields that have values.
 */

import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
  UserIcon,
  ShieldIcon,
  TrendingUpIcon,
  TargetIcon,
  WalletIcon,
  GraduationCapIcon,
} from "lucide-react";
import type { IntentProfile } from "@/lib/types";

interface UserProfileCardProps {
  profile: IntentProfile;
}

const lifeStageLabels: Record<string, string> = {
  early_career: "Early Career",
  mid_career: "Mid Career",
  pre_retirement: "Pre-Retirement",
  retired: "Retired",
};

const riskIcons = {
  conservative: ShieldIcon,
  moderate: TargetIcon,
  aggressive: TrendingUpIcon,
};

const riskColors = {
  conservative: "bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-300",
  moderate: "bg-amber-100 text-amber-800 dark:bg-amber-900/30 dark:text-amber-300",
  aggressive: "bg-rose-100 text-rose-800 dark:bg-rose-900/30 dark:text-rose-300",
};

const experienceLabels: Record<string, string> = {
  beginner: "Beginner",
  intermediate: "Intermediate",
  experienced: "Experienced",
};

export function UserProfileCard({ profile }: UserProfileCardProps) {
  const hasAnyData =
    profile.life_stage ||
    profile.risk_preference ||
    profile.investment_experience ||
    profile.current_assets;

  if (!hasAnyData) {
    return null;
  }

  const RiskIcon = profile.risk_preference ? riskIcons[profile.risk_preference] : null;

  return (
    <Card className="border-0 bg-card shadow-sm">
      <CardContent className="pt-4 space-y-3">
        <p className="text-xs font-medium uppercase tracking-wider text-muted-foreground">
          User Profile
        </p>

        <div className="grid gap-3">
          {/* Life Stage */}
          {profile.life_stage && (
            <div className="flex items-center gap-3">
              <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-secondary">
                <UserIcon className="h-4 w-4 text-muted-foreground" />
              </div>
              <div>
                <p className="text-xs text-muted-foreground">Life Stage</p>
                <p className="text-sm font-medium">
                  {lifeStageLabels[profile.life_stage] || profile.life_stage}
                </p>
              </div>
            </div>
          )}

          {/* Risk Preference */}
          {profile.risk_preference && RiskIcon && (
            <div className="flex items-center gap-3">
              <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-secondary">
                <RiskIcon className="h-4 w-4 text-muted-foreground" />
              </div>
              <div>
                <p className="text-xs text-muted-foreground">Risk Tolerance</p>
                <Badge
                  variant="secondary"
                  className={`${riskColors[profile.risk_preference]} border-0 font-medium capitalize text-xs`}
                >
                  {profile.risk_preference}
                </Badge>
              </div>
            </div>
          )}

          {/* Investment Experience */}
          {profile.investment_experience && (
            <div className="flex items-center gap-3">
              <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-secondary">
                <GraduationCapIcon className="h-4 w-4 text-muted-foreground" />
              </div>
              <div>
                <p className="text-xs text-muted-foreground">Experience</p>
                <p className="text-sm font-medium">
                  {experienceLabels[profile.investment_experience] || profile.investment_experience}
                </p>
              </div>
            </div>
          )}

          {/* Current Assets */}
          {profile.current_assets && (
            <div className="flex items-center gap-3">
              <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-secondary">
                <WalletIcon className="h-4 w-4 text-muted-foreground" />
              </div>
              <div>
                <p className="text-xs text-muted-foreground">Assets</p>
                <p className="text-sm font-medium">{profile.current_assets}</p>
              </div>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
```

**Step 4: Run TypeScript check**

Run: `cd frontend && npm run type-check`
Expected: No errors

**Step 5: Commit**

```bash
git add frontend/components/assistant-ui/user-profile-card.tsx
git commit -m "$(cat <<'EOF'
feat(ui): add UserProfileCard component

Display user profile fields extracted from conversation:
- Life Stage, Risk Tolerance, Experience, Assets
Only renders when at least one field has data.

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>
EOF
)"
```

---

## Task 10: Create FinancialGoalCard Component (Frontend)

**Files:**
- Create: `frontend/components/assistant-ui/financial-goal-card.tsx`

**Step 1: No test needed (UI component)**

**Step 2: Skip**

**Step 3: Write implementation**

Create `frontend/components/assistant-ui/financial-goal-card.tsx`:

```typescript
"use client";

/**
 * FinancialGoalCard - Displays user's financial goal extracted from conversation.
 * Only renders when at least one goal field has data.
 */

import { Card, CardContent } from "@/components/ui/card";
import { CakeIcon, WalletIcon, ClockIcon, TargetIcon } from "lucide-react";
import type { FinancialGoal } from "@/lib/types";

interface FinancialGoalCardProps {
  goal: FinancialGoal | null;
}

const goalTypeLabels: Record<string, string> = {
  retirement: "Retirement",
  wealth_growth: "Wealth Growth",
  education: "Education",
  house: "Home Purchase",
};

export function FinancialGoalCard({ goal }: FinancialGoalCardProps) {
  if (!goal) {
    return null;
  }

  const hasAnyData =
    goal.target_age || goal.target_amount || goal.timeline || goal.goal_type;

  if (!hasAnyData) {
    return null;
  }

  return (
    <Card className="border-0 bg-card shadow-sm">
      <CardContent className="pt-4 space-y-3">
        <div className="flex items-center gap-2">
          <TargetIcon className="h-4 w-4 text-amber-500" />
          <p className="text-xs font-medium uppercase tracking-wider text-muted-foreground">
            Financial Goal
          </p>
        </div>

        <div className="grid gap-3">
          {/* Target Age */}
          {goal.target_age && (
            <div className="flex items-center gap-3">
              <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-secondary">
                <CakeIcon className="h-4 w-4 text-muted-foreground" />
              </div>
              <div>
                <p className="text-xs text-muted-foreground">Target Age</p>
                <p className="text-sm font-medium">{goal.target_age} years old</p>
              </div>
            </div>
          )}

          {/* Target Amount */}
          {goal.target_amount && (
            <div className="flex items-center gap-3">
              <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-secondary">
                <WalletIcon className="h-4 w-4 text-muted-foreground" />
              </div>
              <div>
                <p className="text-xs text-muted-foreground">Target Amount</p>
                <p className="text-sm font-medium">{goal.target_amount}</p>
              </div>
            </div>
          )}

          {/* Timeline */}
          {goal.timeline && (
            <div className="flex items-center gap-3">
              <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-secondary">
                <ClockIcon className="h-4 w-4 text-muted-foreground" />
              </div>
              <div>
                <p className="text-xs text-muted-foreground">Timeline</p>
                <p className="text-sm font-medium">{goal.timeline}</p>
              </div>
            </div>
          )}

          {/* Goal Type */}
          {goal.goal_type && (
            <div className="flex items-center gap-3">
              <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-secondary">
                <TargetIcon className="h-4 w-4 text-muted-foreground" />
              </div>
              <div>
                <p className="text-xs text-muted-foreground">Goal Type</p>
                <p className="text-sm font-medium">
                  {goalTypeLabels[goal.goal_type] || goal.goal_type}
                </p>
              </div>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
```

**Step 4: Run TypeScript check**

Run: `cd frontend && npm run type-check`
Expected: No errors

**Step 5: Commit**

```bash
git add frontend/components/assistant-ui/financial-goal-card.tsx
git commit -m "$(cat <<'EOF'
feat(ui): add FinancialGoalCard component

Display financial goal fields:
- Target Age, Target Amount, Timeline, Goal Type
Only renders when at least one field has data.

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>
EOF
)"
```

---

## Task 11: Create SignalHistory Component (Frontend)

**Files:**
- Create: `frontend/components/assistant-ui/signal-history.tsx`

**Step 1: No test needed (UI component)**

**Step 2: Skip**

**Step 3: Write implementation**

Create `frontend/components/assistant-ui/signal-history.tsx`:

```typescript
"use client";

/**
 * SignalHistory - Collapsible list showing intent signals captured during conversation.
 * Shows most recent 10 signals.
 */

import { useState } from "react";
import { Card, CardContent } from "@/components/ui/card";
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible";
import { Badge } from "@/components/ui/badge";
import { ChevronDownIcon, ScrollTextIcon } from "lucide-react";
import { cn } from "@/lib/utils";
import type { IntentSignal } from "@/lib/types";

interface SignalHistoryProps {
  signals: IntentSignal[];
}

const signalTypeColors = {
  explicit: "bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-300",
  inferred: "bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-300",
  clarified: "bg-purple-100 text-purple-800 dark:bg-purple-900/30 dark:text-purple-300",
};

function formatTimestamp(timestamp: string): string {
  try {
    const date = new Date(timestamp);
    return date.toLocaleTimeString("en-US", {
      hour: "2-digit",
      minute: "2-digit",
      hour12: false,
    });
  } catch {
    return "";
  }
}

function formatConfidence(confidence: number): string {
  return `${Math.round(confidence * 100)}%`;
}

export function SignalHistory({ signals }: SignalHistoryProps) {
  const [isOpen, setIsOpen] = useState(false);

  if (signals.length === 0) {
    return null;
  }

  // Show most recent 10 signals
  const displaySignals = signals.slice(-10).reverse();

  return (
    <Card className="border-0 bg-card shadow-sm">
      <Collapsible open={isOpen} onOpenChange={setIsOpen}>
        <CollapsibleTrigger asChild>
          <CardContent className="pt-4 pb-4 cursor-pointer hover:bg-secondary/50 transition-colors">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <ScrollTextIcon className="h-4 w-4 text-muted-foreground" />
                <p className="text-xs font-medium uppercase tracking-wider text-muted-foreground">
                  Signal History
                </p>
                <Badge variant="secondary" className="text-xs">
                  {signals.length}
                </Badge>
              </div>
              <ChevronDownIcon
                className={cn(
                  "h-4 w-4 text-muted-foreground transition-transform",
                  isOpen && "rotate-180"
                )}
              />
            </div>
          </CardContent>
        </CollapsibleTrigger>

        <CollapsibleContent>
          <div className="px-4 pb-4">
            <div className="space-y-2 max-h-64 overflow-y-auto">
              {displaySignals.map((signal, index) => (
                <div
                  key={index}
                  className="flex items-start justify-between py-2 border-b border-border/50 last:border-0"
                >
                  <div className="space-y-1">
                    <div className="flex items-center gap-2">
                      <span className="text-xs text-muted-foreground font-mono">
                        {formatTimestamp(signal.timestamp)}
                      </span>
                      <span className="text-sm font-medium capitalize">
                        {signal.category.replace(/_/g, " ")}
                      </span>
                    </div>
                    <div className="flex items-center gap-2">
                      <Badge
                        variant="secondary"
                        className={cn(
                          "text-xs border-0",
                          signalTypeColors[signal.signal_type]
                        )}
                      >
                        {signal.signal_type}
                      </Badge>
                      <span className="text-xs text-muted-foreground">
                        {formatConfidence(signal.confidence)}
                      </span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </CollapsibleContent>
      </Collapsible>
    </Card>
  );
}
```

**Step 4: Run TypeScript check**

Run: `cd frontend && npm run type-check`
Expected: No errors

**Step 5: Commit**

```bash
git add frontend/components/assistant-ui/signal-history.tsx
git commit -m "$(cat <<'EOF'
feat(ui): add SignalHistory collapsible component

Display captured intent signals with:
- Timestamp, category, signal type, confidence
- Collapsed by default, shows recent 10 signals
- Color-coded signal type badges

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>
EOF
)"
```

---

## Task 12: Create SessionStats Component (Frontend)

**Files:**
- Create: `frontend/components/assistant-ui/session-stats.tsx`

**Step 1: No test needed (UI component)**

**Step 2: Skip**

**Step 3: Write implementation**

Create `frontend/components/assistant-ui/session-stats.tsx`:

```typescript
"use client";

/**
 * SessionStats - Simple display showing conversation turns and signals count.
 */

import { MessageSquareIcon, ZapIcon } from "lucide-react";

interface SessionStatsProps {
  turnCount: number;
  signalCount: number;
}

export function SessionStats({ turnCount, signalCount }: SessionStatsProps) {
  return (
    <div className="flex items-center justify-center gap-6 py-3 px-4 text-xs text-muted-foreground border-t border-border/50">
      <div className="flex items-center gap-1.5">
        <MessageSquareIcon className="h-3.5 w-3.5" />
        <span>Turns: {turnCount}</span>
      </div>
      <div className="w-px h-4 bg-border" />
      <div className="flex items-center gap-1.5">
        <ZapIcon className="h-3.5 w-3.5" />
        <span>Signals: {signalCount}</span>
      </div>
    </div>
  );
}
```

**Step 4: Run TypeScript check**

Run: `cd frontend && npm run type-check`
Expected: No errors

**Step 5: Commit**

```bash
git add frontend/components/assistant-ui/session-stats.tsx
git commit -m "$(cat <<'EOF'
feat(ui): add SessionStats component

Simple footer showing:
- Conversation turns count
- Captured signals count

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>
EOF
)"
```

---

## Task 13: Refactor IntentProfilePanel to Integrate All Components (Frontend)

**Files:**
- Modify: `frontend/components/assistant-ui/intent-profile-panel.tsx`

**Step 1: No test needed (UI refactor)**

**Step 2: Skip**

**Step 3: Write implementation**

Replace `frontend/components/assistant-ui/intent-profile-panel.tsx`:

```typescript
"use client";

/**
 * IntentProfilePanel - Shows the user's evolving intent profile
 * with User Profile, Financial Goal, Signal History, and Session Stats.
 */

import { useIntentProfile } from "@/lib/intent-profile-context";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { SparklesIcon } from "lucide-react";
import { UserProfileCard } from "./user-profile-card";
import { FinancialGoalCard } from "./financial-goal-card";
import { SignalHistory } from "./signal-history";
import { SessionStats } from "./session-stats";

export function IntentProfilePanel() {
  const { profile, turnCount } = useIntentProfile();
  const intentPercentage = Math.round(profile.intent_score * 100);

  const hasProfileData =
    profile.life_stage ||
    profile.risk_preference ||
    profile.investment_experience ||
    profile.current_assets ||
    profile.financial_goal ||
    profile.product_interests.length > 0;

  return (
    <div className="flex flex-col h-full">
      {/* Scrollable content */}
      <div className="flex-1 overflow-y-auto space-y-5 p-1">
        {/* Header */}
        <div className="flex items-center gap-3 px-1">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-br from-amber-400 to-amber-600 shadow-lg">
            <SparklesIcon className="h-5 w-5 text-white" />
          </div>
          <div>
            <h2 className="text-lg font-semibold tracking-tight">Your Profile</h2>
            <p className="text-xs text-muted-foreground">
              Insights from our conversation
            </p>
          </div>
        </div>

        {/* Intent Score Card */}
        <Card className="overflow-hidden border-0 bg-gradient-to-br from-card to-secondary/30 shadow-sm">
          <CardHeader className="pb-3">
            <CardTitle className="flex items-center justify-between text-sm font-medium text-muted-foreground">
              <span>Intent Clarity</span>
              <span className="font-mono text-2xl font-bold text-foreground tabular-nums">
                {intentPercentage}%
              </span>
            </CardTitle>
          </CardHeader>
          <CardContent className="pb-4">
            <div className="relative h-2.5 w-full overflow-hidden rounded-full bg-muted">
              <div
                className="intent-progress absolute inset-y-0 left-0 rounded-full transition-all duration-500 ease-out"
                style={{ width: `${intentPercentage}%` }}
              />
            </div>
            <p className="mt-3 text-xs text-muted-foreground">
              {intentPercentage < 30 && "Let's learn more about your goals"}
              {intentPercentage >= 30 &&
                intentPercentage < 60 &&
                "Building a clearer picture of your needs"}
              {intentPercentage >= 60 &&
                intentPercentage < 80 &&
                "Good understanding of your preferences"}
              {intentPercentage >= 80 && "Ready for personalized recommendations"}
            </p>
          </CardContent>
        </Card>

        {/* User Profile Card */}
        <UserProfileCard profile={profile} />

        {/* Financial Goal Card */}
        <FinancialGoalCard goal={profile.financial_goal} />

        {/* Product Interests */}
        {profile.product_interests.length > 0 && (
          <Card className="border-0 bg-card shadow-sm">
            <CardContent className="pt-4">
              <p className="mb-3 text-xs font-medium uppercase tracking-wider text-muted-foreground">
                Interests
              </p>
              <div className="flex flex-wrap gap-2">
                {profile.product_interests.map((interest) => (
                  <Badge
                    key={interest}
                    variant="outline"
                    className="border-border/50 bg-secondary/50 font-normal capitalize"
                  >
                    {interest.replace(/_/g, " ")}
                  </Badge>
                ))}
              </div>
            </CardContent>
          </Card>
        )}

        {/* Signal History */}
        <SignalHistory signals={profile.signals} />

        {/* Empty State */}
        {!hasProfileData && profile.signals.length === 0 && (
          <div className="rounded-xl border border-dashed border-border/50 bg-muted/30 p-6 text-center">
            <div className="mx-auto mb-3 flex h-12 w-12 items-center justify-center rounded-full bg-secondary">
              <SparklesIcon className="h-5 w-5 text-muted-foreground" />
            </div>
            <p className="text-sm font-medium text-foreground">Share your story</p>
            <p className="mt-1 text-xs text-muted-foreground">
              Tell me about your financial goals and I'll help build your profile
            </p>
          </div>
        )}
      </div>

      {/* Fixed footer */}
      <SessionStats turnCount={turnCount} signalCount={profile.signals.length} />
    </div>
  );
}
```

**Step 4: Run TypeScript check and dev server**

Run: `cd frontend && npm run type-check && npm run dev`
Expected: No errors, app runs at localhost:3000

**Step 5: Commit**

```bash
git add frontend/components/assistant-ui/intent-profile-panel.tsx
git commit -m "$(cat <<'EOF'
feat(ui): refactor IntentProfilePanel with all new components

Integrate new components into IntentProfilePanel:
- UserProfileCard (life stage, risk, experience, assets)
- FinancialGoalCard (target age, amount, timeline)
- SignalHistory (collapsible signal list)
- SessionStats (turns and signals count)

Layout with scrollable content and fixed footer.

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>
EOF
)"
```

---

## Task 14: Wire Turn Count Increment in Chat Flow (Frontend)

**Files:**
- Modify: `frontend/lib/runtime-provider.tsx` (or wherever chat messages are handled)

**Step 1: No test needed (integration)**

**Step 2: Skip**

**Step 3: Find and update the chat message handler**

Look for where `onNew` or message sending happens and add `incrementTurnCount()` call:

```typescript
// In the chat runtime or message handler:
const { incrementTurnCount } = useIntentProfile();

// When user sends a message:
const onNew = async (message) => {
  incrementTurnCount(); // Add this line
  // ... existing message handling
};
```

**Step 4: Test manually**

Send messages and verify turn count increments in the Session Stats.

**Step 5: Commit**

```bash
git add frontend/lib/runtime-provider.tsx
git commit -m "$(cat <<'EOF'
feat(runtime): increment turn count on user message

Wire incrementTurnCount() to run when user sends a message,
enabling Session Stats to show accurate turn count.

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>
EOF
)"
```

---

## Verification Checklist

After completing all tasks:

- [ ] Backend tests pass: `uv run pytest tests/agent/intent_chat/ -v`
- [ ] Frontend type-check passes: `cd frontend && npm run type-check`
- [ ] Backend runs: `uv run uvicorn agent_will_smith.main:app --reload`
- [ ] Frontend runs: `cd frontend && npm run dev`
- [ ] Manual test: Send message mentioning retirement age and amount, verify:
  - Intent score increases
  - User Profile shows life stage
  - Financial Goal shows target age and amount
  - Signal History shows captured signal
  - Session Stats shows turns and signals count

---

## Dependency Order

```
Task 1 (FinancialGoal) → Task 2 (IntentProfile) → Task 3 (intent_capture_tool)
    → Task 4 (tool_execution_node) → Task 5 (response_node) → Task 6 (system prompt)
                    ↓
Task 7 (types.ts) → Task 8 (context)
                    ↓
Task 9, 10, 11, 12 (UI components - can be parallel)
                    ↓
Task 13 (IntentProfilePanel refactor) → Task 14 (wire turn count)
```
