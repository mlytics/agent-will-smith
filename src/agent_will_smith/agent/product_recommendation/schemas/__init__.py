"""Agent schemas organized by concern.

Structure:
- state.py: LangGraph state (AgentState - Pydantic)
- messages.py: Node input/output messages and context
- database.py: Vector search result DTOs (for parsing raw results)

All schemas use Pydantic for runtime validation and type safety.
"""

# State
from src.agent.product_recommendation.schemas.state import AgentState

# Messages (node outputs and agent context)
from src.agent.product_recommendation.schemas.messages import (
    AgentContext,
    ProductResult,
    AgentResponse,
    IntentAnalysisOutput,
    VerticalSearchResult,
    ParallelSearchOutput,
    ComposeResponseOutput,
    AgentOutput,
)

# Database DTOs (vector search results)
from src.agent.product_recommendation.schemas.database import (
    ActivityDTO,
    BookDTO,
    ArticleDTO,
)

__all__ = [
    # State
    "AgentState",
    # Messages
    "AgentContext",
    "ProductResult",
    "AgentResponse",
    "IntentAnalysisOutput",
    "VerticalSearchResult",
    "ParallelSearchOutput",
    "ComposeResponseOutput",
    "AgentOutput",
    # Database DTOs
    "ActivityDTO",
    "BookDTO",
    "ArticleDTO",
]

