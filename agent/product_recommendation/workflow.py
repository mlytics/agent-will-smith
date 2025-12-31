"""Product recommendation workflow composition.

Defines and compiles the LangGraph workflow for product recommendations.
This is where all nodes are wired together with dependencies injected.
"""

from functools import lru_cache, partial
from langgraph.graph import StateGraph, START, END
import structlog

from agent.product_recommendation.schemas import AgentState
from agent.product_recommendation.node import (
    intent_analysis_node,
    parallel_search_node,
    compose_response_node,
)
from agent.product_recommendation.infra.llm_client import get_llm_client
from agent.product_recommendation.infra.vector_search import get_vector_search_client

logger = structlog.get_logger(__name__)


@lru_cache()
def get_workflow() -> StateGraph:
    """Get compiled workflow with dependencies injected.
    
    Creates workflow with all dependencies baked in using functools.partial.
    This allows LangGraph nodes to receive dependencies without global imports.
    
    Thread-safe singleton using @lru_cache.
    
    Returns:
        Compiled StateGraph with dependencies injected
    """
    logger.info("building_workflow_with_dependencies")
    
    # Get pooled dependencies (從小組到大)
    vector_client = get_vector_search_client()
    llm = get_llm_client()
    
    # Inject dependencies into nodes using functools.partial
    intent_node_with_deps = partial(
        intent_analysis_node,
        llm_client=llm
    )
    
    search_node_with_deps = partial(
        parallel_search_node,
        vector_client=vector_client
    )
    
    # compose_response_node is pure function (no external dependencies)
    
    # Build workflow with injected nodes
    workflow = StateGraph(AgentState)
    workflow.add_node("intent_analysis", intent_node_with_deps)
    workflow.add_node("parallel_search", search_node_with_deps)
    workflow.add_node("compose_response", compose_response_node)
    
    # Connect nodes
    workflow.add_edge(START, "intent_analysis")
    workflow.add_edge("intent_analysis", "parallel_search")
    workflow.add_edge("parallel_search", "compose_response")
    workflow.add_edge("compose_response", END)
    
    logger.info("workflow_with_dependencies_built")
    
    return workflow.compile()


__all__ = [
    "get_workflow",
]

