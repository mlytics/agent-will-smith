"""Agent-specific schemas for product recommendation agent.

Contains:
- ProductResult: Domain model for search results (Pydantic for type safety)
- AgentInput: Input DTO AND namespace model (dual purpose)
- AgentOutput: Output DTO AND namespace model (dual purpose)

All schemas use Pydantic for runtime validation and type safety.
Namespaced state schemas are in schemas/state.py.
"""

from typing import Literal, Optional
from pydantic import BaseModel, Field
from agent_will_smith.agent.product_recommendation.schemas.types import VERTICALS


class ProductResult(BaseModel):
    """Structured result from vector search tools.

    Follows guideline: "Tools return structured data, not English."
    Pydantic validation ensures data integrity at boundaries.

    This model is kept as Pydantic throughout the LangGraph state
    and only converted to dict at the API boundary.
    """

    product_id: str = Field(..., min_length=1, description="Unique product identifier")
    product_type: Literal["activity", "book", "article"] = Field(..., description="Product type")  # Singular form
    title: str = Field(..., min_length=1, description="Product title")
    description: Optional[str] = Field(None, description="Product description")
    relevance_score: float = Field(..., ge=0.0, le=1.0, description="Relevance score from vector search")
    metadata: dict = Field(default_factory=dict, description="Product-specific metadata")


# =============================================================================
# Agent Input/Output DTOs (Dual Purpose: Agent Boundary + State Namespace)
# =============================================================================

class AgentInput(BaseModel):
    """Input DTO AND namespace model (dual purpose).

    Used for:
    1. agent.invoke() parameter type (API boundary)
    2. state.input namespace (internal state)

    Owner: Agent (from API request)
    Lifecycle: Set once at start, never modified
    """
    article: str = Field(..., min_length=10)
    question: str = Field(..., min_length=5)
    k: int = Field(..., ge=1, le=10, description="Products per vertical")
    verticals: list[VERTICALS]
    customer_uuid: Optional[str] = None


class AgentOutput(BaseModel):
    """Output DTO AND namespace model (dual purpose).

    Used for:
    1. agent.invoke() return type (API boundary)
    2. state.output namespace (internal state)

    Note: ProductResult objects are converted to dicts by OutputNode.
    """
    grouped_results: dict[str, list[dict]] = Field(..., description="Products grouped by vertical")
    total_products: int = Field(..., ge=0, description="Total products found")
    status: Literal["complete", "partial"] = Field(..., description="Execution status")
    errors: dict[str, str] = Field(default_factory=dict, description="Errors by vertical")
    intent: str = Field(..., min_length=10, description="Intent analysis summary")
