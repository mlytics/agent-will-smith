"""Pydantic models for conversation analytics.

Contains Scenario, TestSession, and ConversationTurn models for tracking
conversation testing sessions and analytics data.
"""

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field


class Scenario(BaseModel):
    """Predefined conversation scenario for testing.

    Attributes:
        scenario_id: Unique identifier for the scenario.
        name: Display name of the scenario.
        icon: Emoji or icon for UI display.
        short_desc: Brief description of the scenario.
        persona_description: Detailed persona description for the test user.
        expected_intents: List of intent categories expected to be captured.
        expected_life_stage: Expected life stage to be inferred.
        expected_risk_preference: Expected risk preference to be inferred.
    """

    scenario_id: str = Field(
        ...,
        description="Unique identifier for the scenario",
        min_length=1,
        max_length=50,
        examples=["cxo_wealth"],
    )
    name: str = Field(
        ...,
        description="Display name of the scenario",
        min_length=1,
        max_length=100,
        examples=["High-Level Executive Wealth Planning"],
    )
    icon: str = Field(
        ...,
        description="Emoji or icon name for UI display (e.g., FontAwesome icon name)",
        min_length=1,
        max_length=50,
        examples=["briefcase", "graduation-cap"],
    )
    short_desc: str = Field(
        ...,
        description="Brief description of the scenario",
        min_length=1,
        max_length=500,
        examples=["52-year-old CFO planning for retirement and wealth transfer"],
    )
    persona_description: Optional[str] = Field(
        default=None,
        description="Detailed persona description for the test user",
        max_length=2000,
    )
    expected_intents: list[str] = Field(
        default_factory=list,
        description="List of intent categories expected to be captured",
        examples=[["retirement", "wealth_management", "tax_planning"]],
    )
    expected_life_stage: Optional[str] = Field(
        default=None,
        description="Expected life stage to be inferred",
        max_length=50,
        examples=["pre_retirement"],
    )
    expected_risk_preference: Optional[str] = Field(
        default=None,
        description="Expected risk preference to be inferred",
        max_length=50,
        examples=["moderate"],
    )


class TestSession(BaseModel):
    """A conversation testing session.

    Attributes:
        session_id: Unique identifier for the session (UUID format).
        scenario_id: ID of the scenario being tested.
        created_at: Timestamp when the session was created.
        ended_at: Timestamp when the session ended (None if still active).
        final_intent_profile: Final intent profile at session end.
        turn_count: Number of conversation turns in the session.
        inferred_scenario: Scenario inferred by the system (for comparison).
    """

    session_id: str = Field(
        ...,
        description="Unique identifier for the session",
        min_length=1,
        max_length=100,
        examples=["550e8400-e29b-41d4-a716-446655440000"],
    )
    scenario_id: str = Field(
        ...,
        description="ID of the scenario being tested",
        min_length=1,
        max_length=50,
        examples=["cxo_wealth"],
    )
    created_at: datetime = Field(
        ...,
        description="Timestamp when the session was created",
    )
    ended_at: Optional[datetime] = Field(
        default=None,
        description="Timestamp when the session ended",
    )
    final_intent_profile: Optional[dict[str, Any]] = Field(
        default=None,
        description="Final intent profile at session end",
    )
    turn_count: int = Field(
        default=0,
        description="Number of conversation turns in the session",
        ge=0,
    )
    inferred_scenario: Optional[str] = Field(
        default=None,
        description="Scenario inferred by the system",
        max_length=50,
    )


class ConversationTurn(BaseModel):
    """A single turn in a conversation.

    Attributes:
        id: Auto-incremented database ID (None before insertion).
        session_id: ID of the session this turn belongs to.
        turn_number: Sequential turn number within the session (1-indexed).
        timestamp: Timestamp when the turn occurred.
        user_message: The user's message text.
        assistant_response: The assistant's response text.
        response_time_ms: Response time in milliseconds.
        tool_calls: List of tool calls made during this turn.
        intent_profile_snapshot: Snapshot of intent profile after this turn.
    """

    id: Optional[int] = Field(
        default=None,
        description="Auto-incremented database ID",
    )
    session_id: str = Field(
        ...,
        description="ID of the session this turn belongs to",
        min_length=1,
        max_length=100,
    )
    turn_number: int = Field(
        ...,
        description="Sequential turn number within the session",
        ge=1,
    )
    timestamp: datetime = Field(
        ...,
        description="Timestamp when the turn occurred",
    )
    user_message: str = Field(
        ...,
        description="The user's message text",
        min_length=1,
        max_length=10000,
    )
    assistant_response: str = Field(
        ...,
        description="The assistant's response text",
        min_length=1,
        max_length=50000,
    )
    response_time_ms: int = Field(
        ...,
        description="Response time in milliseconds",
        ge=0,
    )
    tool_calls: list[dict[str, Any]] = Field(
        default_factory=list,
        description="List of tool calls made during this turn",
    )
    intent_profile_snapshot: dict[str, Any] = Field(
        default_factory=dict,
        description="Snapshot of intent profile after this turn",
    )
