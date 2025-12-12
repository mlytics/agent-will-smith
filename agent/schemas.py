"""Agent-specific schemas for state management and responses.

Follows guideline: "Make state schema explicit early."
Uses dataclasses (compatible with Pydantic) for type safety.
"""

from dataclasses import dataclass
from typing import Literal


@dataclass
class AgentContext:
    """Custom runtime context for the agent.

    This context is passed to tools via ToolRuntime and provides
    access to request-scoped information.
    """

    trace_id: str
    article: str
    question: str
    max_k: int
    product_types: list[Literal["activities", "books"]] | None = None


@dataclass
class ProductResult:
    """Structured result from vector search tools.

    Follows guideline: "Tools return structured data, not English."
    """

    product_id: str
    product_type: Literal["activity", "book"]
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

