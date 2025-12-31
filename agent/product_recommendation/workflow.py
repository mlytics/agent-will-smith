"""Product recommendation workflow composition.

Defines and compiles the LangGraph workflow for product recommendations.
This is where all nodes are wired together with dependencies injected.

Uses explicit dependency injection - all dependencies passed as parameters.
"""

from functools import partial
from langgraph.graph import StateGraph, START, END
from databricks.vector_search.client import VectorSearchClient
from databricks_langchain import ChatDatabricks
import structlog

from agent.product_recommendation.schemas import AgentState
from agent.product_recommendation.node import (
    intent_analysis_node,
    parallel_search_node,
    compose_response_node,
)

logger = structlog.get_logger(__name__)


def create_workflow(
    vector_client: VectorSearchClient,
    llm_client: ChatDatabricks,
) -> StateGraph:
    """Create compiled workflow with explicit dependency injection.
    
    All dependencies are passed as parameters (explicit DI).
    No hidden singleton calls - true dependency injection pattern.
    
    This function is called once at server startup with pooled resources.
    
    Args:
        vector_client: Pooled VectorSearchClient from server startup
        llm_client: Pooled ChatDatabricks client from server startup
    
    Returns:
        Compiled StateGraph with dependencies baked into nodes
    """
    logger.info("building_workflow_with_explicit_dependencies")
    
    # Inject dependencies into nodes using functools.partial
    # Dependencies are passed in from server startup (explicit DI)
    intent_node_with_deps = partial(
        intent_analysis_node,
        llm_client=llm_client  # From parameter (explicit)
    )
    
    search_node_with_deps = partial(
        parallel_search_node,
        vector_client=vector_client  # From parameter (explicit)
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
    
    logger.info("workflow_with_explicit_dependencies_built")
    
    return workflow.compile()


__all__ = [
    "create_workflow",
]

