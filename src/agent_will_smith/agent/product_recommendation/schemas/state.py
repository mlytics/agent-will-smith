"""LangGraph state schema for product recommendation agent with namespaced architecture.

Architecture:
- Each node gets its own namespace in the state
- Nodes can only WRITE to their own namespace
- Nodes can READ from any namespace
- Pydantic validation throughout (no dict conversions in state)

See schemas/messages.py for additional agent schemas.
"""

from typing import Literal, Optional
from pydantic import BaseModel, Field
from agent_will_smith.agent.product_recommendation.schemas.types import VERTICALS
from agent_will_smith.agent.product_recommendation.schemas.messages import ProductResult


# ============================================================================
# NAMESPACE MODELS (Sub-states for each node)
# ============================================================================

class InputsNamespace(BaseModel):
    """
    Namespace: inputs
    Owner: Agent (from API request)
    Lifecycle: Set once at start, never modified
    """
    article: str = Field(..., min_length=10)
    question: str = Field(..., min_length=5)
    k: int = Field(..., ge=1, le=10, description="Products per vertical")
    verticals: list[VERTICALS]
    customer_uuid: Optional[str] = None


class IntentNodeNamespace(BaseModel):
    """
    Namespace: intent_node
    Owner: IntentAnalysisNode
    Lifecycle: Written once by intent_analysis_node
    """
    intent: str = Field(
        ...,
        min_length=10,
        max_length=1000,
        description="LLM-generated intent analysis"
    )


class SearchNodeNamespace(BaseModel):
    """
    Namespace: search_node
    Owner: ParallelSearchNode
    Lifecycle: Written once by parallel_search_node
    """
    # Core results: Dict mapping vertical -> products (keep as Pydantic objects!)
    results: dict[VERTICALS, list[ProductResult]] = Field(
        default_factory=dict,
        description="Search results grouped by vertical (Pydantic objects, not dicts)"
    )

    # Execution metadata
    status: Literal["complete", "partial"] = "complete"
    errors: dict[str, str] = Field(
        default_factory=dict,
        description="Map of vertical -> error message for failures"
    )


class ComposeNodeNamespace(BaseModel):
    """
    Namespace: compose_node
    Owner: ComposeResponseNode
    Lifecycle: Written once by compose_response_node
    """
    # Final curated results (top K, sorted)
    grouped_results: dict[VERTICALS, list[ProductResult]] = Field(
        default_factory=dict,
        description="Top K products per vertical, sorted by relevance (Pydantic objects)"
    )
    total_products: int = 0


# ============================================================================
# MAIN STATE MODEL
# ============================================================================

class AgentState(BaseModel):
    """
    Main LangGraph state with explicit node namespaces.

    Architecture:
    - Each namespace is owned by one node
    - Nodes only WRITE to their own namespace
    - Nodes can READ from any namespace

    Data Flow:
    inputs → intent_node → search_node → compose_node

    Benefits of Pydantic state:
    - Runtime validation at every state update
    - Early error detection
    - Type safety throughout workflow
    - Clear ownership via namespaces
    """

    # Node namespaces
    inputs: InputsNamespace
    intent_node: Optional[IntentNodeNamespace] = None
    search_node: Optional[SearchNodeNamespace] = None
    compose_node: Optional[ComposeNodeNamespace] = None

    class Config:
        # Allow arbitrary types for LangGraph compatibility
        arbitrary_types_allowed = True
