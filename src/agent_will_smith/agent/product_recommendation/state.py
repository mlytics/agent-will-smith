"""LangGraph state schemas for product recommendation agent.

Contains AgentInput, AgentOutput, and AgentState for workflow orchestration.
"""

from typing import Literal, Optional
from pydantic import BaseModel, Field
from agent_will_smith.agent.product_recommendation.model.types import Vertical
from agent_will_smith.agent.product_recommendation.model.namespaces import (
    IntentNodeNamespace,
    SearchNodeNamespace,
)


class AgentInput(BaseModel):
    """Input DTO for agent invocation and state namespace.
    
    Note: Validation is handled at the API boundary (RecommendProductsRequest).
    This DTO trusts that inputs are already validated.
    """
    article: str = Field(..., description="Original article text to analyze for product recommendations")
    question: str = Field(..., description="User question guiding the recommendation intent")
    k: int = Field(..., description="Number of products to return per vertical")
    verticals: list[Vertical] = Field(..., description="Product verticals to search (activities, books, articles)")
    customer_uuid: Optional[str] = Field(None, description="Customer UUID for multi-tenant data isolation")


class AgentOutput(BaseModel):
    """Output DTO for agent return and state namespace.
    
    Note: Internal state model - validation happens at API response layer.
    """
    grouped_results: dict[str, list[dict]] = Field(..., description="Products grouped by vertical with metadata")
    total_products: int = Field(..., description="Total number of products across all verticals")
    status: Literal["complete", "partial"] = Field(..., description="Search status: 'complete' if all verticals succeeded, 'partial' if some failed")
    errors: dict[str, str] = Field(default_factory=dict, description="Errors by vertical name if any searches failed")
    intent: str = Field(..., description="LLM-analyzed user intent from article and question")


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
