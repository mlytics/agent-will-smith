"""LangGraph workflow for product recommendation.

Connects all nodes into an executable workflow graph.
Architecture: Linear flow, no conditionals (user controls verticals).
"""

from langgraph.graph import StateGraph, START, END
import structlog

from agent.product_recommendation.schemas import AgentState
from agent.product_recommendation.node import (
    intent_analysis_node,
    parallel_search_node,
    compose_response_node,
)

logger = structlog.get_logger(__name__)


def create_recommendation_workflow() -> StateGraph:
    """Create the product recommendation LangGraph workflow.
    
    Flow:
        START → intent_analysis → parallel_search → compose_response → END
    
    Architecture:
    - Linear flow (no conditionals)
    - User controls which verticals to search
    - Single LLM call (intent analysis)
    - Parallel vector search across verticals
    - Deterministic response composition
    
    Returns:
        Compiled StateGraph ready for execution
    """
    logger.info("creating_workflow")
    
    # Define graph with AgentState
    workflow = StateGraph(AgentState)
    
    # Add nodes
    workflow.add_node("intent_analysis", intent_analysis_node)
    workflow.add_node("parallel_search", parallel_search_node)
    workflow.add_node("compose_response", compose_response_node)
    
    # Connect nodes (linear flow - no conditionals!)
    workflow.add_edge(START, "intent_analysis")
    workflow.add_edge("intent_analysis", "parallel_search")
    workflow.add_edge("parallel_search", "compose_response")
    workflow.add_edge("compose_response", END)
    
    logger.info("workflow_created",
               nodes=["intent_analysis", "parallel_search", "compose_response"])
    
    return workflow.compile()


# Singleton workflow instance
_workflow = None


def get_workflow() -> StateGraph:
    """Get compiled workflow (singleton pattern).
    
    Returns:
        Compiled workflow ready for execution
    """
    global _workflow
    if _workflow is None:
        logger.info("initializing_workflow_singleton")
        _workflow = create_recommendation_workflow()
    return _workflow

