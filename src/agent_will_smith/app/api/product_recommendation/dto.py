"""API request/response schemas for product recommendation.

Follows guideline: "Prefer typed outputs at every boundary."
All API boundaries use Pydantic models for validation and documentation.
"""

from typing import Literal

from pydantic import BaseModel, Field

from agent_will_smith.agent.product_recommendation.model.types import Vertical


class RecommendProductsRequest(BaseModel):
    """Request schema for product recommendation endpoint."""

    article: str = Field(
        ...,
        description="Original article text to analyze",
        min_length=10,
        max_length=50000,
        examples=["This article discusses sustainable living and eco-friendly products..."],
    )
    question: str = Field(
        ...,
        description="Selected question to guide recommendations",
        min_length=5,
        max_length=500,
        examples=["What products would help someone live more sustainably?"],
    )
    k: int = Field(
        ...,
        description="Number of products to recommend per vertical",
        ge=1,
        le=10,
        examples=[5],
    )
    product_types: list[Vertical] = Field(
        ...,
        description="Product types to search (e.g., ['activities'], ['books'], or multiple)",
        examples=[["activities"], ["activities", "books"]],
        min_length=1,
    )
    customer_uuid: str = Field(
        ...,
        description="Customer UUID for multi-tenant data isolation",
        examples=["0b8ecbe2-6097-4ca8-b61b-dfeb1578b011"],
    )


class ProductRecommendation(BaseModel):
    """Individual product recommendation with metadata."""

    product_id: str = Field(..., description="Unique product identifier")
    vertical: Vertical = Field(
        ..., description="Product vertical (activities, books, or articles)"
    )
    title: str = Field(..., description="Product title")
    description: str | None = Field(None, description="Product description")
    relevance_score: float = Field(
        ..., description="Relevance score (0.0-1.0)", ge=0.0, le=1.0
    )
    metadata: dict = Field(
        default_factory=dict, description="Additional product-specific metadata"
    )


class VerticalResults(BaseModel):
    """Results for a single vertical."""

    vertical: str = Field(..., description="Vertical name (activities, books, or articles)")
    products: list[ProductRecommendation] = Field(
        ..., description="Products for this vertical (top K)"
    )
    count: int = Field(..., description="Number of products in this vertical")
    error: str | None = Field(None, description="Error message if vertical search failed")


class RecommendProductsResponse(BaseModel):
    """Response schema for product recommendation endpoint (grouped by vertical)."""

    results_by_vertical: list[VerticalResults] = Field(
        ..., description="Results grouped by vertical (activities, books, articles)"
    )
    total_products: int = Field(..., description="Total number of products across all verticals")
    reasoning: str = Field(..., description="Agent's reasoning/intent analysis")
    status: Literal["complete", "partial"] = Field(
        ..., description="Status: 'complete' if all verticals succeeded, 'partial' if some failed"
    )
    verticals_searched: list[str] = Field(..., description="List of verticals that were searched")
