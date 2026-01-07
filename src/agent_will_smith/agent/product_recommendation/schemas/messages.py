"""Agent-specific schemas for state management and responses.

Follows guideline: "Make state schema explicit early."

Contains:
- LangGraph State (TypedDict for workflow state)
- Node Messages (Pydantic for validation at every boundary)
- Database DTOs (Pydantic for vector search results)

All schemas use Pydantic for runtime validation and type safety.
"""

from typing import Literal
from pydantic import BaseModel, Field
from agent_will_smith.agent.product_recommendation.schemas.types import VERTICALS


class ProductResult(BaseModel):
    """Structured result from vector search tools.

    Follows guideline: "Tools return structured data, not English."
    Pydantic validation ensures data integrity at boundaries.
    """

    product_id: str = Field(..., min_length=1, description="Unique product identifier")
    product_type: Literal["activity", "book", "article"] = Field(..., description="Product type")  # Singular form
    title: str = Field(..., min_length=1, description="Product title")
    description: str | None = Field(None, description="Product description")
    relevance_score: float = Field(..., ge=0.0, le=1.0, description="Relevance score from vector search")
    metadata: dict = Field(default_factory=dict, description="Product-specific metadata")


# =============================================================================
# Node Message Schemas (Pydantic - validates all node inputs/outputs)
# =============================================================================

class IntentAnalysisOutput(BaseModel):
    """Output from intent analysis node.
    
    Validated output ensures intent is non-empty and reasonable length.
    """
    intent: str = Field(..., min_length=10, max_length=1000, description="Intent analysis summary")


class VerticalSearchResult(BaseModel):
    """Result from searching a single vertical.
    
    Used internally in parallel search to ensure type safety.
    """
    vertical: VERTICALS = Field(..., description="Vertical that was searched")
    products: list[dict] = Field(default_factory=list, description="Product results (ProductResult.model_dump())")
    error: str | None = Field(None, description="Error message if search failed")


class ParallelSearchOutput(BaseModel):
    """Output from parallel search node.
    
    Validates all search results and error tracking.
    """
    activities: list[dict] = Field(default_factory=list, description="Activity search results")
    books: list[dict] = Field(default_factory=list, description="Book search results")
    articles: list[dict] = Field(default_factory=list, description="Article search results")
    errors: dict[str, str] = Field(default_factory=dict, description="Errors by vertical")
    status: Literal["complete", "partial"] = Field(..., description="Search status")


class ComposeResponseOutput(BaseModel):
    """Output from response composer node.

    Validates final grouped results structure.
    """
    grouped_results: dict[str, list[dict]] = Field(..., description="Results grouped by vertical")
    total_products: int = Field(..., ge=0, description="Total products across all verticals")


class AgentOutput(BaseModel):
    """Final output from recommend_products agent.
    
    This is the complete agent response with all information.
    Validates the agent's final output before returning to API layer.
    """
    grouped_results: dict[str, list[dict]] = Field(..., description="Products grouped by vertical")
    total_products: int = Field(..., ge=0, description="Total products found")
    status: Literal["complete", "partial"] = Field(..., description="Execution status")
    errors: dict[str, str] = Field(default_factory=dict, description="Errors by vertical")
    intent: str = Field(..., min_length=10, description="Intent analysis summary")


# =============================================================================
# LangGraph State Schema (Pydantic - validates at every state update!)
# =============================================================================
