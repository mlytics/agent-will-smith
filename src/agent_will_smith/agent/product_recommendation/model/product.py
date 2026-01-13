"""Product domain model."""

from typing import Optional
from pydantic import BaseModel, Field

from agent_will_smith.agent.product_recommendation.model.types import VERTICALS


class ProductResult(BaseModel):
    """Domain model for product search results.
    
    Created by repository layer to provide unified interface
    across different product types (activities, books, articles).
    """
    product_id: str = Field(
        ...,
        description="Unique identifier for the product",
        min_length=1,
        max_length=100,
        examples=["act-123", "book-456", "article-789"],
    )
    vertical: VERTICALS = Field(
        ...,
        description="Product vertical (activities, books, or articles)",
        examples=["activities"],
    )
    title: str = Field(
        ...,
        description="Product title",
        min_length=1,
        max_length=500,
        examples=["Sustainable Living Workshop"],
    )
    description: Optional[str] = Field(
        None,
        description="Product description or summary",
        max_length=5000,
        examples=["Learn practical skills for sustainable living in this hands-on workshop..."],
    )
    relevance_score: float = Field(
        ...,
        description="Vector search relevance score (0.0=least relevant, 1.0=most relevant)",
        ge=0.0,
        le=1.0,
        examples=[0.87],
    )
    metadata: dict = Field(
        default_factory=dict,
        description="Additional product-specific metadata (location, authors, prices, etc.)",
        examples=[{"location_name": "San Francisco", "category": "environment"}],
    )
