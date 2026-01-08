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
from agent_will_smith.agent.product_recommendation.schemas.messages import ProductResult, AgentInput, AgentOutput


# ============================================================================
# NAMESPACE MODELS (Internal node namespaces)
# ============================================================================
# Note: AgentInput and AgentOutput (dual-purpose DTOs) are in messages.py

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


# ============================================================================
# LANGGRAPH INPUT/OUTPUT STATE SCHEMAS (Subsets of AgentState)
# ============================================================================

class AgentInputState(BaseModel):
    """Input schema for LangGraph - declares which fields are inputs."""
    input: AgentInput  # Singular!


class AgentOutputState(BaseModel):
    """Output schema for LangGraph - declares which fields are outputs."""
    output: AgentOutput  # Singular!


# ============================================================================
# MAIN STATE MODEL
# ============================================================================

class AgentState(BaseModel):
    """Main LangGraph state with namespaced architecture.

    Architecture:
    - Each namespace is owned by one node
    - Nodes only WRITE to their own namespace
    - Nodes can READ from any namespace

    Data Flow:
    input → intent_node → search_node → output

    Namespaces:
    - input: AgentInput DTO (special - dual purpose)
    - intent_node: Intent analysis output (IntentNodeNamespace)
    - search_node: Search results (SearchNodeNamespace)
    - output: AgentOutput DTO (special - dual purpose)

    Benefits of Pydantic state:
    - Runtime validation at every state update
    - Early error detection
    - Type safety throughout workflow
    - Clear ownership via namespaces
    """

    # Input/output namespaces (dual-purpose DTOs)
    input: AgentInput  # SINGULAR! (not inputs)
    output: Optional[AgentOutput] = None  # SINGULAR! Written by OutputNode

    # Internal node namespaces
    intent_node: Optional[IntentNodeNamespace] = None
    search_node: Optional[SearchNodeNamespace] = None
