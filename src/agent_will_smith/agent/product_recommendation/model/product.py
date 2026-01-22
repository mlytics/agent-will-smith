"""Product domain model with typed metadata."""

from pydantic import BaseModel, Field

from agent_will_smith.agent.product_recommendation.model.types import Vertical


# =============================================================================
# Typed Metadata Classes (one per product vertical)
# Note: Internal models created from validated repo DTOs - trusted data.
# =============================================================================

class ActivityMetadata(BaseModel):
    """Activity-specific metadata fields (explicit, type-safe)."""
    category: str | None = Field(None, description="Activity category")
    organizer: str | None = Field(None, description="Event organizer name")
    location_name: str | None = Field(None, description="Venue or location name")
    location_address: str | None = Field(None, description="Full address")
    start_time: str | None = Field(None, description="Activity start time (ISO 8601)")
    end_time: str | None = Field(None, description="Activity end time (ISO 8601)")
    permalink_url: str | None = Field(None, description="URL to activity details")
    cover_image_urls: list[str] = Field(default_factory=list, description="List of cover image URLs")


class BookMetadata(BaseModel):
    """Book-specific metadata fields (explicit, type-safe)."""
    title_subtitle: str | None = Field(None, description="Book subtitle")
    authors: list[str] = Field(default_factory=list, description="List of author names")
    categories: list[str] = Field(default_factory=list, description="Book categories/genres")
    permalink_url: str | None = Field(None, description="URL to book details")
    cover_image_url: str | None = Field(None, description="Cover image URL")
    prices: list[str] = Field(default_factory=list, description="List of prices")


class ArticleMetadata(BaseModel):
    """Article-specific metadata fields (explicit, type-safe)."""
    authors: list[str] = Field(default_factory=list, description="List of article authors")
    keywords: list[str] = Field(default_factory=list, description="Article keywords/tags")
    categories: list[str] = Field(default_factory=list, description="Article categories")
    permalink_url: str | None = Field(None, description="URL to article")
    thumbnail_url: str | None = Field(None, description="Thumbnail image URL")
    main_image_url: str | None = Field(None, description="Main article image URL")
    publish_time: str | None = Field(None, description="Article publish time (ISO 8601)")


# Type alias for metadata union
ProductMetadata = ActivityMetadata | BookMetadata | ArticleMetadata


# =============================================================================
# ProductResult Domain Model
# =============================================================================

class ProductResult(BaseModel):
    """Domain model for product search results.
    
    Created by repository layer to provide unified interface
    across different product types (activities, books, articles).
    Metadata is typed per vertical for type safety and explicitness.
    
    Note: Created internally from validated repo DTOs - trusted data.
    """
    product_id: str = Field(..., description="Unique identifier for the product")
    vertical: Vertical = Field(..., description="Product vertical (activities, books, or articles)")
    title: str = Field(..., description="Product title")
    description: str | None = Field(None, description="Product description or summary")
    relevance_score: float = Field(..., description="Vector search relevance score (higher is more similar)")
    metadata: ProductMetadata = Field(..., description="Product-specific metadata (typed per vertical)")
