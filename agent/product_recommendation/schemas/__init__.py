"""Agent schemas organized by concern.

Structure:
- state.py: LangGraph state (AgentState - Pydantic)
- messages.py: Node input/output messages and context

All schemas use Pydantic for runtime validation and type safety.
"""

# State
from agent.product_recommendation.schemas.state import AgentState

# Messages (node outputs and agent context)
from agent.product_recommendation.schemas.messages import (
    AgentContext,
    ProductResult,
    AgentResponse,
    IntentAnalysisOutput,
    VerticalSearchResult,
    ParallelSearchOutput,
    ComposeResponseOutput,
    PromptContent,
    AgentOutput,
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
    "PromptContent",
    "AgentOutput",
]

