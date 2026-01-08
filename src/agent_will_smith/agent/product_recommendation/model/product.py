"""Product domain model."""

from typing import Literal, Optional
from pydantic import BaseModel, Field


class ProductResult(BaseModel):
    """Domain model for product search results.
    
    Created by repository layer to provide unified interface
    across different product types (activities, books, articles).
    """
    product_id: str = Field(..., min_length=1)
    product_type: Literal["activity", "book", "article"]
    title: str = Field(..., min_length=1)
    description: Optional[str] = None
    relevance_score: float = Field(..., ge=0.0, le=1.0)
    metadata: dict = Field(default_factory=dict)
