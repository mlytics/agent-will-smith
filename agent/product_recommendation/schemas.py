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


class AgentContext(BaseModel):
    """Custom runtime context for the agent.

    This context is passed to tools via ToolRuntime and provides
    access to request-scoped information.
    
    NOTE: Currently only used by @tool decorated functions.
    """

    trace_id: str = Field(..., min_length=1, description="Trace ID for request tracking")
    article: str = Field(..., min_length=10, description="Article text to analyze")
    question: str = Field(..., min_length=5, description="Question to guide search")
    max_k: int = Field(..., ge=1, le=100, description="Maximum results to return")
    product_types: list[VERTICALS] | None = Field(
        default=None, description="Product types to search"
    )


class ProductResult(BaseModel):
    """Structured result from vector search tools.

    Follows guideline: "Tools return structured data, not English."
    Pydantic validation ensures data integrity at boundaries.
    """

    product_id: str = Field(..., min_length=1, description="Unique product identifier")
    product_type: Literal["activity", "book", "article"] = Field(..., description="Product type")  # Singular form
    title: str = Field(..., min_length=1, description="Product title")
    description: str | None = Field(None, description="Product description")
    relevance_score: float = Field(..., ge=0.0, le=1.0, description="Relevance score from vector search")
    metadata: dict = Field(default_factory=dict, description="Product-specific metadata")


class AgentResponse(BaseModel):
    """Structured response format from the agent.

    This is the final output that gets converted to the API response.
    Follows guideline: "Prefer typed outputs at every boundary."
    """

    products: list[ProductResult] = Field(..., description="List of recommended products")
    reasoning: str = Field(..., min_length=1, description="Agent's reasoning")
    total_searched: int = Field(..., ge=0, description="Total products searched")


# =============================================================================
# Node Message Schemas (Pydantic - validates all node inputs/outputs)
# =============================================================================

class IntentAnalysisOutput(BaseModel):
    """Output from intent analysis node.
    
    Validated output ensures intent is non-empty and reasonable length.
    """
    intent: str = Field(..., min_length=10, max_length=1000, description="Intent analysis summary")


class VerticalSearchResult(BaseModel):
    """Result from searching a single vertical.
    
    Used internally in parallel search to ensure type safety.
    """
    vertical: VERTICALS = Field(..., description="Vertical that was searched")
    products: list[dict] = Field(default_factory=list, description="Product results (ProductResult.model_dump())")
    error: str | None = Field(None, description="Error message if search failed")


class ParallelSearchOutput(BaseModel):
    """Output from parallel search node.
    
    Validates all search results and error tracking.
    """
    activities: list[dict] = Field(default_factory=list, description="Activity search results")
    books: list[dict] = Field(default_factory=list, description="Book search results")
    articles: list[dict] = Field(default_factory=list, description="Article search results")
    errors: dict[str, str] = Field(default_factory=dict, description="Errors by vertical")
    status: Literal["complete", "partial"] = Field(..., description="Search status")


class ComposeResponseOutput(BaseModel):
    """Output from response composer node.
    
    Validates final grouped results structure.
    """
    grouped_results: dict[str, list[dict]] = Field(..., description="Results grouped by vertical")
    total_products: int = Field(..., ge=0, description="Total products across all verticals")


class PromptContent(BaseModel):
    """Validated prompt content from MLflow.
    
    Ensures loaded prompts are non-empty and reasonable.
    """
    text: str = Field(..., min_length=50, max_length=10000, description="Prompt text from MLflow registry")
    source: str = Field(..., description="Prompt source URI (e.g., prompts:/...)")


class AgentOutput(BaseModel):
    """Final output from recommend_products agent.
    
    This is the complete agent response with all information.
    Validates the agent's final output before returning to API layer.
    """
    grouped_results: dict[str, list[dict]] = Field(..., description="Products grouped by vertical")
    total_products: int = Field(..., ge=0, description="Total products found")
    status: Literal["complete", "partial"] = Field(..., description="Execution status")
    errors: dict[str, str] = Field(default_factory=dict, description="Errors by vertical")
    intent: str = Field(..., min_length=10, description="Intent analysis summary")


# =============================================================================
# LangGraph State Schema (Pydantic - validates at every state update!)
# =============================================================================

class AgentState(BaseModel):
    """LangGraph workflow state with Pydantic validation.
    
    This state is passed between nodes in the LangGraph workflow.
    LangGraph 0.2.x supports Pydantic BaseModel for automatic validation.
    
    Flow:
        Input → Intent Analysis → Parallel Search → Compose Response
        
    Benefits of Pydantic state:
    - Runtime validation at every state update
    - Early error detection
    - Type safety throughout workflow
    """
    # Input (from API request) - Required
    article: str = Field(..., min_length=10)
    question: str = Field(..., min_length=5)
    k: int = Field(..., ge=1, le=10)
    verticals: list[VERTICALS]
    trace_id: str = Field(..., min_length=1)
    customer_uuid: str | None = None
    
    # Intent Analysis Output (from LLM) - Optional
    intent: str | None = None
    
    # Search Results (full objects, no hydration needed) - Optional
    activities: list[dict] = Field(default_factory=list)
    books: list[dict] = Field(default_factory=list)
    articles: list[dict] = Field(default_factory=list)
    
    # Status Tracking - Optional
    status: Literal["complete", "partial"] = "complete"
    errors: dict[str, str] = Field(default_factory=dict)
    
    # Final Output (from compose node) - Optional
    grouped_results: dict[str, list[dict]] = Field(default_factory=dict)
    total_products: int = 0


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
