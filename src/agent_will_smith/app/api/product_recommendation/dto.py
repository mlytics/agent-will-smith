"""API request/response schemas for product recommendation.

Follows guideline: "Prefer typed outputs at every boundary."
All API boundaries use Pydantic models for validation and documentation.
"""

from typing import Literal

from pydantic import BaseModel, Field, model_validator

from agent_will_smith.agent.product_recommendation.model.types import Vertical
from agent_will_smith.agent.product_recommendation.model.product import ProductMetadata


class RecommendProductsRequest(BaseModel):
    """Request schema for product recommendation endpoint."""

    article: str = Field(
        ...,
        description="Original article text to analyze",
        min_length=0,
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
    product_types: dict[Vertical, list[str]] = Field(
        ...,
        description="Product types to search with customer UUIDs per vertical",
        examples=[{
            "articles": ["0b8ecbe2-6097-4ca8-b61b-dfeb1578b011"],
            "books": ["738c9f0b-d795-4520-979a-2b6dddc1c5a4"],
            "activities": ["0b8ecbe2-6097-4ca8-b61b-dfeb1578b011"],
        }],
    )

    @model_validator(mode="after")
    def validate_product_types(self) -> "RecommendProductsRequest":
        """Validate each vertical has at least one customer UUID."""
        if not self.product_types:
            raise ValueError("product_types must contain at least one vertical")
        for vertical, uuids in self.product_types.items():
            if not uuids:
                raise ValueError(
                    f"product_types[{vertical.value}] must contain at least one customer UUID"
                )
        return self


class ProductRecommendation(BaseModel):
    """Individual product recommendation with typed metadata."""

    product_id: str = Field(..., description="Unique product identifier")
    vertical: Vertical = Field(
        ..., description="Product vertical (activities, books, or articles)"
    )
    title: str = Field(..., description="Product title")
    description: str | None = Field(None, description="Product description")
    relevance_score: float = Field(..., description="Relevance score (higher is more similar)")
    metadata: ProductMetadata = Field(
        ..., description="Product-specific metadata (typed per vertical)"
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
