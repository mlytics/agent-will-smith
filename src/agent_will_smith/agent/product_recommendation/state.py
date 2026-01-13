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
    article: str = Field(
        ...,
        description="Original article text to analyze for product recommendations",
        min_length=10,
        max_length=50000,
        examples=["This article discusses sustainable living and eco-friendly products for modern households..."],
    )
    question: str = Field(
        ...,
        description="User question guiding the recommendation intent",
        min_length=5,
        max_length=500,
        examples=["What products would help someone live more sustainably?"],
    )
    k: int = Field(
        ...,
        description="Number of products to return per vertical",
        examples=[5],
    )
    verticals: list[VERTICALS] = Field(
        ...,
        description="Product verticals to search (activities, books, articles)",
        min_length=1,
        examples=[["activities", "books"]],
    )
    customer_uuid: Optional[str] = Field(
        None,
        description="Customer UUID for multi-tenant data isolation",
        pattern=r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$",
        examples=["0b8ecbe2-6097-4ca8-b61b-dfeb1578b011"],
    )


class AgentOutput(BaseModel):
    """Output DTO for agent return and state namespace."""
    grouped_results: dict[str, list[dict]] = Field(
        ...,
        description="Products grouped by vertical with metadata",
        examples=[{"activities": [{"product_id": "act-123", "title": "Hiking Tour", "relevance_score": 0.92}]}],
    )
    total_products: int = Field(
        ...,
        description="Total number of products across all verticals",
        ge=0,
        examples=[15],
    )
    status: Literal["complete", "partial"] = Field(
        ...,
        description="Search status: 'complete' if all verticals succeeded, 'partial' if some failed",
        examples=["complete"],
    )
    errors: dict[str, str] = Field(
        default_factory=dict,
        description="Errors by vertical name if any searches failed",
        examples=[{"activities": "UpstreamTimeoutError: Search timed out"}],
    )
    intent: str = Field(
        ...,
        description="LLM-analyzed user intent from article and question",
        min_length=10,
        max_length=1000,
        examples=["User seeks sustainable living products focusing on eco-friendly activities and educational books."],
    )


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
