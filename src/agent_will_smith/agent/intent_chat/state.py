"""LangGraph state schemas for intent chat agent.

Contains ChatInput, ChatOutput, IntentProfile, and ChatState for workflow orchestration.
"""

from datetime import datetime, timezone
from typing import Any, Literal, Optional

from pydantic import BaseModel, Field

from agent_will_smith.agent.intent_chat.model.namespaces import (
    ConversationNodeNamespace,
    ResponseNodeNamespace,
    ToolCallingNodeNamespace,
    ToolExecutionNodeNamespace,
)


class IntentSignal(BaseModel):
    """Represents a detected intent signal from user conversation."""

    signal_type: Literal["explicit", "inferred", "clarified"] = Field(
        ...,
        description="How the intent was detected: explicit (user stated), inferred (from context), clarified (after follow-up)",
        examples=["explicit"],
    )
    category: str = Field(
        ...,
        description="Intent category (e.g., retirement, investment, insurance, travel)",
        min_length=1,
        max_length=100,
        examples=["retirement"],
    )
    confidence: float = Field(
        ...,
        description="Confidence score for this intent signal",
        ge=0.0,
        le=1.0,
        examples=[0.85],
    )
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="When the intent signal was detected",
    )


class IntentProfile(BaseModel):
    """Aggregated intent profile built from conversation signals."""

    life_stage: Optional[str] = Field(
        default=None,
        description="Detected life stage (e.g., early_career, mid_career, pre_retirement, retired)",
        max_length=50,
        examples=["mid_career"],
    )
    risk_preference: Optional[Literal["conservative", "moderate", "aggressive"]] = Field(
        default=None,
        description="User's risk tolerance preference",
    )
    product_interests: list[str] = Field(
        default_factory=list,
        description="List of product categories the user has shown interest in",
        examples=[["retirement_planning", "investment_funds"]],
    )
    intent_score: float = Field(
        default=0.0,
        description="Overall intent score (0.0-1.0) indicating readiness for product recommendation",
        ge=0.0,
        le=1.0,
    )
    signals: list[IntentSignal] = Field(
        default_factory=list,
        description="History of detected intent signals",
    )


class ChatInput(BaseModel):
    """Input DTO for chat agent invocation."""

    message: str = Field(
        ...,
        description="User message text",
        min_length=1,
        max_length=5000,
        examples=["I'm looking for ways to save for retirement."],
    )
    session_id: str = Field(
        ...,
        description="Unique session identifier for conversation continuity",
        pattern=r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$",
        examples=["550e8400-e29b-41d4-a716-446655440000"],
    )
    context: Optional[dict[str, Any]] = Field(
        default=None,
        description="Optional context data (e.g., article content, page metadata)",
        examples=[{"article_id": "art-123", "article_title": "Retirement Planning Guide"}],
    )
    conversation_history: list[dict[str, str]] = Field(
        default_factory=list,
        description="Previous conversation messages with role and content",
        examples=[[{"role": "user", "content": "Hello"}, {"role": "assistant", "content": "Hi! How can I help?"}]],
    )


class ChatOutput(BaseModel):
    """Output DTO for chat agent response."""

    response: str = Field(
        ...,
        description="Assistant's response text",
        min_length=1,
        max_length=50000,
        examples=["Based on your interest in retirement planning, I can recommend some resources..."],
    )
    intent_profile: IntentProfile = Field(
        ...,
        description="Current intent profile built from the conversation",
    )
    tool_calls: list[dict[str, Any]] = Field(
        default_factory=list,
        description="List of tool calls made during this turn",
        examples=[[{"tool": "product_recommendation", "result_count": 5}]],
    )
    session_id: str = Field(
        ...,
        description="Session identifier echoed back for client tracking",
        pattern=r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$",
    )
    is_complete: bool = Field(
        default=True,
        description="Whether the response is complete (False if streaming)",
    )


class ChatInputState(BaseModel):
    """LangGraph input schema for chat agent."""

    input: ChatInput


class ChatOutputState(BaseModel):
    """LangGraph output schema for chat agent."""

    output: ChatOutput


class ChatState(BaseModel):
    """Main LangGraph state with namespaced architecture for chat agent.

    Data flow: input -> conversation_node -> tool_calling_node -> tool_execution_node -> response_node -> output

    Each node reads from any namespace but writes only to its own namespace.
    """

    # Core I/O
    input: ChatInput
    output: Optional[ChatOutput] = None

    # LangChain message list (BaseMessage compatible dicts)
    messages: list[dict[str, Any]] = Field(
        default_factory=list,
        description="LangChain-compatible message list for LLM context",
    )

    # Intent tracking
    intent_profile: IntentProfile = Field(
        default_factory=IntentProfile,
        description="Accumulated intent profile from conversation",
    )

    # Current turn tool calls (for routing decisions)
    current_tool_calls: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Tool calls in the current turn, used for graph routing",
    )

    # Node namespaces
    conversation_node: Optional[ConversationNodeNamespace] = None
    tool_calling_node: Optional[ToolCallingNodeNamespace] = None
    tool_execution_node: Optional[ToolExecutionNodeNamespace] = None
    response_node: Optional[ResponseNodeNamespace] = None
