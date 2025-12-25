"""API request/response schemas.

Follows guideline: "Prefer typed outputs at every boundary."
All API boundaries use Pydantic models for validation and documentation.
"""

from typing import Literal
from pydantic import BaseModel, Field, field_validator


class RecommendProductsRequest(BaseModel):
    """Request schema for product recommendation endpoint."""

    article: str = Field(
        ...,
        description="Original article text to analyze",
        min_length=10,
        examples=["This article discusses sustainable living and eco-friendly products..."],
    )
    question: str = Field(
        ...,
        description="Selected question to guide recommendations",
        min_length=5,
        examples=["What products would help someone live more sustainably?"],
    )
    k: int = Field(
        ...,
        description="Number of products to recommend (1-10)",
        ge=1,
        le=10,
        examples=[5],
    )
    product_types: list[Literal["activities", "books"]] | None = Field(
        default=None,
        description="Filter by product types. If None, search both activities and books.",
        examples=[["activities", "books"]],
    )


class ProductRecommendation(BaseModel):
    """Individual product recommendation with metadata."""

    product_id: str = Field(..., description="Unique product identifier")
    product_type: Literal["activity", "book"] = Field(
        ..., description="Type of product (activity or book)"
    )
    title: str = Field(..., description="Product title")
    description: str | None = Field(None, description="Product description")
    relevance_score: float = Field(
        ..., description="Relevance score (0.0-1.0)", ge=0.0, le=1.0
    )
    reasoning: str = Field(
        ..., description="Agent's reasoning for why this product was recommended"
    )
    metadata: dict = Field(
        default_factory=dict, description="Additional product-specific metadata"
    )


class RecommendProductsResponse(BaseModel):
    """Response schema for product recommendation endpoint."""

    products: list[ProductRecommendation] = Field(
        ..., description="List of recommended products"
    )
    trace_id: str = Field(..., description="Trace ID for request tracking and debugging")
    processing_time_ms: float = Field(..., description="Processing time in milliseconds")

    @field_validator("products")
    @classmethod
    def validate_products_count(cls, v: list[ProductRecommendation]) -> list[ProductRecommendation]:
        """Ensure products list is not empty and within limits."""
        if not v:
            raise ValueError("At least one product must be recommended")
        if len(v) > 10:
            raise ValueError("Cannot recommend more than 10 products")
        return v


class HealthCheckResponse(BaseModel):
    """Health check response schema."""

    status: Literal["healthy", "unhealthy"] = Field(..., description="Service health status")
    version: str = Field(..., description="Application version")
    environment: str = Field(..., description="Environment name")
    timestamp: str = Field(..., description="Current timestamp (ISO 8601)")


class ErrorResponse(BaseModel):
    """Standard error response schema."""

    error: str = Field(..., description="Error message")
    detail: str | None = Field(None, description="Detailed error information (dev only)")
    trace_id: str | None = Field(None, description="Trace ID for debugging")

