"""Product domain model with typed metadata."""

from pydantic import BaseModel, Field

from agent_will_smith.agent.product_recommendation.model.types import Vertical


# =============================================================================
# Typed Metadata Classes (one per product vertical)
# =============================================================================

class ActivityMetadata(BaseModel):
    """Activity-specific metadata fields (explicit, type-safe)."""
    
    category: str | None = Field(None, description="Activity category", examples=["environment", "education"])
    organizer: str | None = Field(None, description="Event organizer name", examples=["EcoLife Foundation"])
    location_name: str | None = Field(None, description="Venue or location name", examples=["Green Community Center"])
    location_address: str | None = Field(None, description="Full address", examples=["123 Eco St, San Francisco, CA"])
    start_time: str | None = Field(None, description="Activity start time (ISO 8601)", examples=["2024-03-15T10:00:00Z"])
    end_time: str | None = Field(None, description="Activity end time (ISO 8601)", examples=["2024-03-15T12:00:00Z"])
    permalink_url: str | None = Field(None, description="URL to activity details", examples=["https://example.com/activities/123"])
    cover_image_urls: list[str] = Field(default_factory=list, description="List of cover image URLs")


class BookMetadata(BaseModel):
    """Book-specific metadata fields (explicit, type-safe)."""
    
    title_subtitle: str | None = Field(None, description="Book subtitle", examples=["A Guide to Eco-Friendly Living"])
    authors: list[str] = Field(default_factory=list, description="List of author names", examples=[["Jane Smith", "John Doe"]])
    categories: list[str] = Field(default_factory=list, description="Book categories/genres", examples=[["Environment", "Lifestyle"]])
    permalink_url: str | None = Field(None, description="URL to book details", examples=["https://example.com/books/123"])
    cover_image_url: str | None = Field(None, description="Cover image URL", examples=["https://example.com/covers/book-123.jpg"])
    prices: list[str] = Field(default_factory=list, description="List of prices", examples=[["$19.99", "$9.99 (ebook)"]])


class ArticleMetadata(BaseModel):
    """Article-specific metadata fields (explicit, type-safe)."""
    
    authors: list[str] = Field(default_factory=list, description="List of article authors", examples=[["Sarah Green"]])
    keywords: list[str] = Field(default_factory=list, description="Article keywords/tags", examples=[["sustainability", "eco-friendly"]])
    categories: list[str] = Field(default_factory=list, description="Article categories", examples=[["Environment", "Lifestyle"]])
    permalink_url: str | None = Field(None, description="URL to article", examples=["https://example.com/articles/123"])
    thumbnail_url: str | None = Field(None, description="Thumbnail image URL", examples=["https://example.com/thumbs/article-123.jpg"])
    main_image_url: str | None = Field(None, description="Main article image URL", examples=["https://example.com/images/article-123.jpg"])
    publish_time: str | None = Field(None, description="Article publish time (ISO 8601)", examples=["2024-01-15T08:00:00Z"])


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
    """
    product_id: str = Field(
        ...,
        description="Unique identifier for the product",
        min_length=1,
        max_length=100,
        examples=["act-123", "book-456", "article-789"],
    )
    vertical: Vertical = Field(
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
    description: str | None = Field(
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
    metadata: ProductMetadata = Field(
        ...,
        description="Product-specific metadata (typed per vertical)",
    )
