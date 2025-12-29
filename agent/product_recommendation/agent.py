"""Product recommendation agent using LangGraph workflow.

Architecture:
- Single LLM call (intent analysis)
- Parallel vector search (user-controlled verticals)
- Deterministic response composition
- No multi-round reasoning

Flow:
    Input → Intent Analysis → Parallel Search → Compose Response → Output
"""

import mlflow
import structlog

from agent.product_recommendation.workflow import get_workflow
from agent.product_recommendation.schemas import AgentState, AgentOutput

logger = structlog.get_logger(__name__)


@mlflow.trace
async def recommend_products(
    article: str,
    question: str,
    k: int,
    trace_id: str,
    verticals: list[str] | None = None,
    customer_uuid: str | None = None,
) -> AgentOutput:
    """Product recommendation agent (LangGraph implementation).
    
    Analyzes article and question, searches requested verticals in parallel,
    and returns grouped product recommendations.
    
    Args:
        article: Article text to analyze
        question: Question to guide recommendations
        k: Number of products to recommend per vertical
        trace_id: Trace ID for observability
        verticals: Which verticals to search (default: all 3)
        customer_uuid: Optional customer UUID for multi-tenant filtering
        
    Returns:
        AgentOutput (Pydantic model) with:
          - grouped_results: {vertical: [products]}
          - total_products: int
          - status: "complete" | "partial"
          - errors: {vertical: error_msg}
          - intent: str
          
    Note: This is an async function (breaking change from v1).
    """
    # Default to all 3 verticals
    if verticals is None:
        verticals = ["activities", "books", "articles"]
    
    logger.info("agent_started",
               trace_id=trace_id,
               article_length=len(article),
               question_length=len(question),
               k=k,
               verticals=verticals,
               customer_uuid=customer_uuid)
    
    # Get workflow
    workflow = get_workflow()
    
    # Initialize state (Pydantic model)
    initial_state = AgentState(
        article=article,
        question=question,
        k=k,
        verticals=verticals,
        trace_id=trace_id,
        customer_uuid=customer_uuid,
    )
    
    logger.info("workflow_invoking",
               trace_id=trace_id,
               workflow_type="product_recommendation")
    
    try:
        # Execute workflow (returns dict, but validated by Pydantic during workflow)
        final_state_dict = await workflow.ainvoke(initial_state)
        
        # Parse back to Pydantic for validation and type-safe access
        final_state = AgentState(**final_state_dict)
        
        logger.info("workflow_completed",
                   trace_id=trace_id,
                   total_products=final_state.total_products,
                   status=final_state.status)
        
        # Convert to AgentOutput
        agent_output = AgentOutput(
            grouped_results=final_state.grouped_results,
            total_products=final_state.total_products,
            status=final_state.status,
            errors=final_state.errors,
            intent=final_state.intent or "No intent provided",
        )
        
        logger.info("agent_completed",
                   trace_id=trace_id,
                   total_products=agent_output.total_products,
                   status=agent_output.status,
                   has_errors=bool(agent_output.errors))
        
        return agent_output  # Return Pydantic model directly
        
    except Exception as e:
        logger.error("agent_execution_failed",
                    trace_id=trace_id,
                    error=str(e),
                    error_type=type(e).__name__,
                    exc_info=True)
        raise
