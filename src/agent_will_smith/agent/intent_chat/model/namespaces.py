"""Node namespace models for LangGraph state in intent chat agent.

Each namespace represents the state owned by a specific node in the graph.
Nodes read from any namespace but write only to their own namespace.
"""

from typing import Any, Optional
from pydantic import BaseModel, Field


class ToolCall(BaseModel):
    """Represents a single tool call from the LLM."""

    id: str = Field(
        ...,
        description="Unique identifier for the tool call",
        min_length=1,
        examples=["call_abc123"],
    )
    name: str = Field(
        ...,
        description="Name of the tool to invoke",
        min_length=1,
        examples=["product_recommendation"],
    )
    args: dict[str, Any] = Field(
        default_factory=dict,
        description="Arguments to pass to the tool",
        examples=[{"article": "...", "question": "...", "k": 5}],
    )


class ToolResult(BaseModel):
    """Represents the result of a tool execution."""

    tool_call_id: str = Field(
        ...,
        description="ID of the tool call this result corresponds to",
        min_length=1,
        examples=["call_abc123"],
    )
    result: Optional[dict[str, Any]] = Field(
        default=None,
        description="Successful result from tool execution",
    )
    error: Optional[str] = Field(
        default=None,
        description="Error message if tool execution failed",
        max_length=2000,
    )


class ConversationNodeNamespace(BaseModel):
    """State namespace for conversation management node.

    Tracks message history updates and token usage for the conversation.
    """

    messages_added: int = Field(
        default=0,
        description="Number of messages added to history in this turn",
        ge=0,
    )
    tokens_used: int = Field(
        default=0,
        description="Estimated tokens used in the current conversation context",
        ge=0,
    )


class ToolCallingNodeNamespace(BaseModel):
    """State namespace for tool calling decision node.

    Tracks tool calls determined by the LLM based on conversation context.
    """

    tool_calls: list[ToolCall] = Field(
        default_factory=list,
        description="List of tool calls requested by the LLM",
    )


class ToolExecutionNodeNamespace(BaseModel):
    """State namespace for tool execution node.

    Tracks results from executing the requested tools.
    """

    tool_results: list[ToolResult] = Field(
        default_factory=list,
        description="Results from tool executions",
    )


class ResponseNodeNamespace(BaseModel):
    """State namespace for response generation node.

    Tracks the final response text and streaming state.
    """

    response_text: str = Field(
        default="",
        description="Generated response text for the user",
        max_length=50000,
    )
    is_streaming: bool = Field(
        default=False,
        description="Whether the response is being streamed",
    )
