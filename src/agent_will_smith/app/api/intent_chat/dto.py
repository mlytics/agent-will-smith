"""API request/response schemas for intent chat.

Follows guideline: "Prefer typed outputs at every boundary."
All API boundaries use Pydantic models for validation and documentation.
"""

from typing import Any, Literal, Optional

from pydantic import BaseModel, Field


class IntentProfileRequest(BaseModel):
    """Intent profile in API request (for state persistence)."""

    life_stage: Optional[str] = Field(
        default=None,
        description="User's life stage (e.g., early_career, mid_career, retirement)",
    )
    risk_preference: Optional[Literal["conservative", "moderate", "aggressive"]] = Field(
        default=None,
        description="User's risk preference",
    )
    product_interests: list[str] = Field(
        default_factory=list,
        description="Products the user has shown interest in",
    )
    intent_score: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Overall intent score (0.0 to 1.0)",
    )


class ChatRequest(BaseModel):
    """Request schema for chat endpoint."""

    message: str = Field(
        ...,
        description="User message to send to the chat agent",
        min_length=1,
        max_length=5000,
        examples=["I'm interested in retirement planning"],
    )
    session_id: str = Field(
        ...,
        description="Session ID for conversation continuity (UUID format)",
        pattern=r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$",
        examples=["550e8400-e29b-41d4-a716-446655440000"],
    )
    context: Optional[dict[str, Any]] = Field(
        default=None,
        description="Optional context for the conversation",
        examples=[{"user_age": 35, "region": "US"}],
    )
    conversation_history: list[dict[str, str]] = Field(
        default_factory=list,
        description="Previous conversation messages for context",
        examples=[[{"role": "user", "content": "Hello"}, {"role": "assistant", "content": "Hi!"}]],
    )
    intent_profile: Optional[IntentProfileRequest] = Field(
        default=None,
        description="Previous intent profile to restore state (sent back from frontend)",
    )


class IntentProfileResponse(BaseModel):
    """Intent profile in API response."""

    life_stage: Optional[str] = Field(
        default=None,
        description="User's life stage (e.g., early_career, mid_career, retirement)",
    )
    risk_preference: Optional[Literal["conservative", "moderate", "aggressive"]] = Field(
        default=None,
        description="User's risk preference",
    )
    product_interests: list[str] = Field(
        default_factory=list,
        description="Products the user has shown interest in",
    )
    intent_score: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Overall intent score (0.0 to 1.0)",
    )


class ChatResponse(BaseModel):
    """Response schema for chat endpoint."""

    response: str = Field(
        ...,
        description="Agent's response message",
    )
    intent_profile: IntentProfileResponse = Field(
        ...,
        description="Current intent profile with user preferences",
    )
    tool_calls: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Tool calls made during this response",
    )
    session_id: str = Field(
        ...,
        description="Session ID for conversation continuity",
    )
    is_complete: bool = Field(
        default=True,
        description="Whether the response is complete (False for streaming)",
    )


class QuickQuestion(BaseModel):
    """A quick question option."""

    id: str = Field(..., description="Unique identifier for the question")
    text: str = Field(..., description="The question text to display")
    category: str = Field(..., description="Category of the question (e.g., retirement, risk)")


class QuickQuestionsResponse(BaseModel):
    """Response schema for quick questions endpoint."""

    questions: list[QuickQuestion] = Field(
        ...,
        description="List of quick question options for the user",
    )
