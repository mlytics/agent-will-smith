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
from agent.product_recommendation.constants import VERTICALS
class ActivityDTO(BaseModel):
    """Activity result from vector search (matches content_activity_gold_index)."""
    
    activity_id: str | None = None
    customer_uuid: str | None = None
    content_id: str
    title: str
    description: str | None = None
    organizer: str | None = None
    category: str | None = None
    location_name: str | None = None
    location_address: str | None = None
    cover_image_urls: list[str] = Field(default_factory=list)
    permalink_url: str | None = None
    start_time: str | None = None  # datetime as string from index
    end_time: str | None = None
    summary: str | None = None
    relevance_score: float = 0.0


class BookDTO(BaseModel):
    """Book result from vector search (matches content_book_gold_index)."""
    
    book_id: str | None = None
    customer_uuid: str | None = None
    content_id: str
    title_main: str
    title_subtitle: str | None = None
    title_original: str | None = None
    description: str | None = None
    categories: list[str] = Field(default_factory=list)
    authors: list[str] = Field(default_factory=list)
    prices: list[str] = Field(default_factory=list)  # JSON strings
    cover_image_url: str | None = None
    permalink_url: str | None = None
    summary: str | None = None
    relevance_score: float = 0.0


class ArticleDTO(BaseModel):
    """Article result from vector search (matches content_article_gold_index)."""
    
    article_id: str | None = None
    customer_uuid: str | None = None
    content_id: str
    title: str
    content: str | None = None  # Full article body text
    authors: list[str] = Field(default_factory=list)
    keywords: list[str] = Field(default_factory=list)
    categories: list[str] = Field(default_factory=list)
    thumbnail_url: str | None = None
    main_image_url: str | None = None
    permalink_url: str | None = None
    publish_time: str | None = None
    summary: str | None = None
    relevance_score: float = 0.0
