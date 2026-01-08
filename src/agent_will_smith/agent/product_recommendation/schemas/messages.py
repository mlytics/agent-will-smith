"""Agent-specific schemas for product recommendation agent.

Contains:
- ProductResult: Domain model for search results (Pydantic for type safety)
- AgentOutput: Final API response schema (converts ProductResult to dict at boundary)

All schemas use Pydantic for runtime validation and type safety.
Namespaced state schemas are in schemas/state.py.
"""

from typing import Literal, Optional
from pydantic import BaseModel, Field


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
# Agent Output Schema (API Boundary)
# =============================================================================

class AgentOutput(BaseModel):
    """Final output from recommend_products agent.

    This is the complete agent response with all information.
    Validates the agent's final output before returning to API layer.

    Note: ProductResult objects are converted to dicts at this boundary.
    """
    grouped_results: dict[str, list[dict]] = Field(..., description="Products grouped by vertical")
    total_products: int = Field(..., ge=0, description="Total products found")
    status: Literal["complete", "partial"] = Field(..., description="Execution status")
    errors: dict[str, str] = Field(default_factory=dict, description="Errors by vertical")
    intent: str = Field(..., min_length=10, description="Intent analysis summary")
