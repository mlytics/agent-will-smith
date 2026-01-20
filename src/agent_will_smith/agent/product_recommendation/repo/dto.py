"""Database DTOs from Databricks vector search.

Raw structures returned from external data sources.
DTOs define their own field mappings to eliminate duplication in registry.
"""

from pydantic import BaseModel, Field


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
    
    @classmethod
    def get_id_field(cls) -> str:
        """Field name for product ID."""
        return "content_id"
    
    @classmethod
    def get_title_field(cls) -> str:
        """Field name for product title."""
        return "title"
    
    @classmethod
    def get_description_field(cls) -> str:
        """Field name for product description."""
        return "description"
    
    @classmethod
    def get_metadata_fields(cls) -> list[str]:
        """Fields to include in metadata (all except core fields and score)."""
        core_fields = {cls.get_id_field(), cls.get_title_field(), cls.get_description_field(), "score"}
        return [field for field in cls.model_fields if field not in core_fields]


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
    
    @classmethod
    def get_id_field(cls) -> str:
        """Field name for product ID."""
        return "content_id"
    
    @classmethod
    def get_title_field(cls) -> str:
        """Field name for product title."""
        return "title_main"
    
    @classmethod
    def get_description_field(cls) -> str:
        """Field name for product description."""
        return "description"
    
    @classmethod
    def get_metadata_fields(cls) -> list[str]:
        """Fields to include in metadata (all except core fields and score)."""
        core_fields = {cls.get_id_field(), cls.get_title_field(), cls.get_description_field(), "score"}
        return [field for field in cls.model_fields if field not in core_fields]


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
    
    @classmethod
    def get_id_field(cls) -> str:
        """Field name for product ID."""
        return "content_id"
    
    @classmethod
    def get_title_field(cls) -> str:
        """Field name for product title."""
        return "title"
    
    @classmethod
    def get_description_field(cls) -> str:
        """Field name for product description."""
        return "content"
    
    @classmethod
    def get_metadata_fields(cls) -> list[str]:
        """Fields to include in metadata (all except core fields and score)."""
        core_fields = {cls.get_id_field(), cls.get_title_field(), cls.get_description_field(), "score"}
        return [field for field in cls.model_fields if field not in core_fields]