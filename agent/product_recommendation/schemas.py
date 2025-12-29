"""Agent-specific schemas for state management and responses.

Follows guideline: "Make state schema explicit early."

Contains:
- LangGraph State (TypedDict for workflow state)
- Agent DTOs (dataclasses for legacy agent compatibility)
- Database DTOs (Pydantic for vector search results)
"""

from dataclasses import dataclass
from typing import TypedDict, Literal, NotRequired
from pydantic import BaseModel, Field
from datetime import datetime


@dataclass
class AgentContext:
    """Custom runtime context for the agent.

    This context is passed to tools via ToolRuntime and provides
    access to request-scoped information.
    
    NOTE: Currently only used by @tool decorated functions (for future LangGraph).
    The simple agent uses direct function calls without ToolRuntime.
    """

    trace_id: str
    article: str
    question: str
    max_k: int
    product_types: list[Literal["activities", "books", "articles"]] | None = None


@dataclass
class ProductResult:
    """Structured result from vector search tools.

    Follows guideline: "Tools return structured data, not English."
    """

    product_id: str
    product_type: Literal["activity", "book", "article"]
    title: str
    description: str | None
    relevance_score: float
    metadata: dict


@dataclass
class AgentResponse:
    """Structured response format from the agent.

    This is the final output that gets converted to the API response.
    Follows guideline: "Prefer typed outputs at every boundary."
    """

    products: list[ProductResult]
    reasoning: str
    total_searched: int


# =============================================================================
# LangGraph State Schema (for future LangGraph workflow)
# =============================================================================

class AgentState(TypedDict):
    """LangGraph workflow state.
    
    This state is passed between nodes in the LangGraph workflow.
    Follows the architecture: user controls which verticals to search.
    
    Flow:
        Input → Intent Analysis → Parallel Search (all requested verticals) → Compose Response
    """
    # Input (from API request)
    article: str
    question: str
    k: int  # Top K products per vertical
    verticals: list[Literal["activities", "books", "articles"]]  # User-specified
    trace_id: str
    customer_uuid: NotRequired[str | None]  # For multi-tenant filtering
    
    # Intent Analysis Output (from LLM)
    intent: NotRequired[str | None]
    
    # Search Results (full objects, no hydration needed)
    # Each vertical stores complete product data
    activities: NotRequired[list[dict]]
    books: NotRequired[list[dict]]
    articles: NotRequired[list[dict]]
    
    # Status Tracking
    status: NotRequired[Literal["complete", "partial"]]
    errors: NotRequired[dict[str, str]]  # {vertical: error_message}
    
    # Final Output (from compose node)
    grouped_results: NotRequired[dict[str, list[dict]]]  # {vertical: products}
    total_products: NotRequired[int]


# =============================================================================
# Database DTOs (Pydantic models matching vector index schemas)
# =============================================================================

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
