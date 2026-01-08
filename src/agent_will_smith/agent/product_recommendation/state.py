"""LangGraph state schemas for product recommendation agent.

Contains AgentInput, AgentOutput, and AgentState for workflow orchestration.
"""

from typing import Literal, Optional
from pydantic import BaseModel, Field
from agent_will_smith.agent.product_recommendation.model.types import VERTICALS
from agent_will_smith.agent.product_recommendation.model.namespaces import (
    IntentNodeNamespace,
    SearchNodeNamespace,
)


class AgentInput(BaseModel):
    """Input DTO for agent invocation and state namespace."""
    article: str = Field(..., min_length=10)
    question: str = Field(..., min_length=5)
    k: int = Field(..., ge=1, le=10)
    verticals: list[VERTICALS]
    customer_uuid: Optional[str] = None


class AgentOutput(BaseModel):
    """Output DTO for agent return and state namespace."""
    grouped_results: dict[str, list[dict]]
    total_products: int = Field(..., ge=0)
    status: Literal["complete", "partial"]
    errors: dict[str, str] = Field(default_factory=dict)
    intent: str = Field(..., min_length=10)


class AgentInputState(BaseModel):
    """LangGraph input schema."""
    input: AgentInput


class AgentOutputState(BaseModel):
    """LangGraph output schema."""
    output: AgentOutput


class AgentState(BaseModel):
    """Main LangGraph state with namespaced architecture.
    
    Data flow: input → intent_node → search_node → output
    """
    input: AgentInput
    output: Optional[AgentOutput] = None
    intent_node: Optional[IntentNodeNamespace] = None
    search_node: Optional[SearchNodeNamespace] = None
