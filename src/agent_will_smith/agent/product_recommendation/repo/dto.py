"""Database DTOs from Databricks vector search.

Raw structures returned from external data sources.
Each DTO knows how to transform itself to ProductResult (explicit, type-safe).
"""

from pydantic import BaseModel, Field

from agent_will_smith.agent.product_recommendation.model.product import (
    ActivityMetadata,
    ArticleMetadata,
    BookMetadata,
    ProductResult,
)
from agent_will_smith.agent.product_recommendation.model.types import Vertical


class ActivityDTO(BaseModel):
    """Activity result from vector search (content_activity_gold_index)."""
    
    content_id: str = Field(..., description="Unique activity identifier", examples=["act-12345"])
    title: str = Field(..., description="Activity title", examples=["Sustainable Living Workshop"])
    description: str | None = Field(None, description="Activity description", examples=["Learn eco-friendly practices"])
    category: str | None = Field(None, description="Activity category", examples=["environment", "education"])
    location_name: str | None = Field(None, description="Venue or location name", examples=["Green Community Center"])
    location_address: str | None = Field(None, description="Full address", examples=["123 Eco St, San Francisco, CA"])
    organizer: str | None = Field(None, description="Event organizer name", examples=["EcoLife Foundation"])
    start_time: str | None = Field(None, description="Activity start time (ISO 8601)", examples=["2024-03-15T10:00:00Z"])
    end_time: str | None = Field(None, description="Activity end time (ISO 8601)", examples=["2024-03-15T12:00:00Z"])
    permalink_url: str | None = Field(None, description="URL to activity details", examples=["https://example.com/activities/123"])
    cover_image_urls: list[str] = Field(default_factory=list, description="List of cover image URLs", examples=[["https://example.com/img1.jpg"]])
    score: float = Field(default=0.0, description="Vector search similarity score (0.0-1.0)", ge=0.0, le=1.0, examples=[0.92])
    
    def to_product_result(self, vertical: Vertical) -> ProductResult:
        """Transform DTO to domain ProductResult.
        
        Explicit field mapping with typed metadata - DTO owns its transformation.
        """
        return ProductResult(
            product_id=self.content_id,
            vertical=vertical,
            title=self.title,
            description=self.description,
            relevance_score=self.score,
            metadata=ActivityMetadata(
                category=self.category,
                organizer=self.organizer,
                location_name=self.location_name,
                location_address=self.location_address,
                start_time=self.start_time,
                end_time=self.end_time,
                permalink_url=self.permalink_url,
                cover_image_urls=self.cover_image_urls,
            ),
        )


class BookDTO(BaseModel):
    """Book result from vector search (content_book_gold_index)."""
    
    content_id: str = Field(..., description="Unique book identifier", examples=["book-67890"])
    title_main: str = Field(..., description="Main book title", examples=["The Sustainable Home"])
    title_subtitle: str | None = Field(None, description="Book subtitle", examples=["A Guide to Eco-Friendly Living"])
    description: str | None = Field(None, description="Book description or summary", examples=["Comprehensive guide to sustainable living..."])
    authors: list[str] = Field(default_factory=list, description="List of author names", examples=[["Jane Smith", "John Doe"]])
    categories: list[str] = Field(default_factory=list, description="Book categories/genres", examples=[["Environment", "Lifestyle"]])
    permalink_url: str | None = Field(None, description="URL to book details", examples=["https://example.com/books/123"])
    cover_image_url: str | None = Field(None, description="Cover image URL", examples=["https://example.com/covers/book-123.jpg"])
    prices: list[str] = Field(default_factory=list, description="List of prices (various formats)", examples=[["$19.99", "$9.99 (ebook)"]])
    score: float = Field(default=0.0, description="Vector search similarity score (0.0-1.0)", ge=0.0, le=1.0, examples=[0.88])
    
    def to_product_result(self, vertical: Vertical) -> ProductResult:
        """Transform DTO to domain ProductResult.
        
        Explicit field mapping with typed metadata - DTO owns its transformation.
        Note: title_main maps to title (product-specific naming).
        """
        return ProductResult(
            product_id=self.content_id,
            vertical=vertical,
            title=self.title_main,  # Explicit: title_main → title
            description=self.description,
            relevance_score=self.score,
            metadata=BookMetadata(
                title_subtitle=self.title_subtitle,
                authors=self.authors,
                categories=self.categories,
                permalink_url=self.permalink_url,
                cover_image_url=self.cover_image_url,
                prices=self.prices,
            ),
        )


class ArticleDTO(BaseModel):
    """Article result from vector search (content_article_gold_index)."""
    
    content_id: str = Field(..., description="Unique article identifier", examples=["article-11223"])
    title: str = Field(..., description="Article title", examples=["10 Ways to Live Sustainably"])
    content: str | None = Field(None, description="Article full text or excerpt", examples=["Sustainable living starts with small changes..."])
    authors: list[str] = Field(default_factory=list, description="List of article authors", examples=[["Sarah Green"]])
    keywords: list[str] = Field(default_factory=list, description="Article keywords/tags", examples=[["sustainability", "eco-friendly", "green-living"]])
    categories: list[str] = Field(default_factory=list, description="Article categories", examples=[["Environment", "Lifestyle"]])
    permalink_url: str | None = Field(None, description="URL to article", examples=["https://example.com/articles/123"])
    thumbnail_url: str | None = Field(None, description="Thumbnail image URL", examples=["https://example.com/thumbs/article-123.jpg"])
    main_image_url: str | None = Field(None, description="Main article image URL", examples=["https://example.com/images/article-123.jpg"])
    publish_time: str | None = Field(None, description="Article publish time (ISO 8601)", examples=["2024-01-15T08:00:00Z"])
    score: float = Field(default=0.0, description="Vector search similarity score (0.0-1.0)", ge=0.0, le=1.0, examples=[0.95])
    
    def to_product_result(self, vertical: Vertical) -> ProductResult:
        """Transform DTO to domain ProductResult.
        
        Explicit field mapping with typed metadata - DTO owns its transformation.
        Note: content maps to description (product-specific naming).
        """
        return ProductResult(
            product_id=self.content_id,
            vertical=vertical,
            title=self.title,
            description=self.content,  # Explicit: content → description
            relevance_score=self.score,
            metadata=ArticleMetadata(
                authors=self.authors,
                keywords=self.keywords,
                categories=self.categories,
                permalink_url=self.permalink_url,
                thumbnail_url=self.thumbnail_url,
                main_image_url=self.main_image_url,
                publish_time=self.publish_time,
            ),
        )