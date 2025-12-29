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
from agent.product_recommendation.schemas import AgentState

logger = structlog.get_logger(__name__)


@mlflow.trace
async def recommend_products(
    article: str,
    question: str,
    k: int,
    trace_id: str,
    verticals: list[str] | None = None,
    customer_uuid: str | None = None,
) -> dict:
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
        dict with:
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
    
    # Initialize state
    initial_state: AgentState = {
        "article": article,
        "question": question,
        "k": k,
        "verticals": verticals,
        "trace_id": trace_id,
        "customer_uuid": customer_uuid,
    }
    
    logger.info("workflow_invoking",
               trace_id=trace_id,
               workflow_type="product_recommendation")
    
    try:
        # Execute workflow
        final_state = await workflow.ainvoke(initial_state)
        
        logger.info("workflow_completed",
                   trace_id=trace_id,
                   total_products=final_state.get("total_products", 0),
                   status=final_state.get("status", "unknown"))
        
        # Extract results
        result = {
            "grouped_results": final_state.get("grouped_results", {}),
            "total_products": final_state.get("total_products", 0),
            "status": final_state.get("status", "complete"),
            "errors": final_state.get("errors", {}),
            "intent": final_state.get("intent", ""),
        }
        
        logger.info("agent_completed",
                   trace_id=trace_id,
                   total_products=result["total_products"],
                   status=result["status"],
                   has_errors=bool(result["errors"]))
        
        return result
        
    except Exception as e:
        logger.error("agent_execution_failed",
                    trace_id=trace_id,
                    error=str(e),
                    error_type=type(e).__name__,
                    exc_info=True)
        raise


# Backward compatibility wrapper (sync version for gradual migration)
def recommend_products_sync(
    article: str,
    question: str,
    k: int,
    trace_id: str,
    product_types: list[str] | None = None,
) -> dict:
    """Synchronous wrapper for backward compatibility.
    
    DEPRECATED: Use async recommend_products() directly.
    This wrapper is for gradual migration only.
    
    Args:
        article: Article text
        question: Question text
        k: Number of products per vertical
        trace_id: Trace ID
        product_types: Old parameter name (maps to verticals)
        
    Returns:
        dict with grouped results
    """
    import asyncio
    
    logger.warning("using_deprecated_sync_wrapper",
                  trace_id=trace_id,
                  message="Use async recommend_products() directly")
    
    # Map old parameter name to new
    verticals = product_types
    
    return asyncio.run(recommend_products(
        article=article,
        question=question,
        k=k,
        trace_id=trace_id,
        verticals=verticals,
    ))
