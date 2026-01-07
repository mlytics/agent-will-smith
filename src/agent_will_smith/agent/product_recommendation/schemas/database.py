"""Database DTOs for vector search results.

These DTOs match the structure returned from Databricks vector search indices.
They provide type safety and validation for raw search results.
"""

from pydantic import BaseModel, Field


class ActivityDTO(BaseModel):
    """Activity result from vector search (content_activity_gold_index)."""
    
    content_id: str
    title: str
    description: str | None = None
    category: str | None = None
    location_name: str | None = None
    location_address: str | None = None
    organizer: str | None = None
    start_time: str | None = None
    end_time: str | None = None
    permalink_url: str | None = None
    cover_image_urls: list[str] = Field(default_factory=list)
    score: float = Field(default=0.0, description="Relevance score from vector search")


class BookDTO(BaseModel):
    """Book result from vector search (content_book_gold_index)."""
    
    content_id: str
    title_main: str
    title_subtitle: str | None = None
    description: str | None = None
    authors: list[str] = Field(default_factory=list)
    categories: list[str] = Field(default_factory=list)
    permalink_url: str | None = None
    cover_image_url: str | None = None
    prices: list[str] = Field(default_factory=list)
    score: float = Field(default=0.0, description="Relevance score from vector search")


class ArticleDTO(BaseModel):
    """Article result from vector search (content_article_gold_index)."""
    
    content_id: str
    title: str
    content: str | None = None  # Full article text
    authors: list[str] = Field(default_factory=list)
    keywords: list[str] = Field(default_factory=list)
    categories: list[str] = Field(default_factory=list)
    permalink_url: str | None = None
    thumbnail_url: str | None = None
    main_image_url: str | None = None
    publish_time: str | None = None
    score: float = Field(default=0.0, description="Relevance score from vector search")

