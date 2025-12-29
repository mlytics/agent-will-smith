"""Parallel vector search node for LangGraph workflow.

Searches all requested verticals in parallel with timeout handling.
Architecture: Deterministic function-based tools, no LLM decision-making.
"""

import asyncio
from typing import Literal
import structlog

from agent.product_recommendation.schemas import AgentState
from agent.product_recommendation.node.query_builder import build_search_query
from agent.product_recommendation.infra.vector_search import (
    search_activities_direct,
    search_books_direct,
    search_articles_direct,
)
from core.exceptions import VectorSearchTimeout, VectorSearchError

logger = structlog.get_logger(__name__)

# Timeout per vertical search (5 seconds)
VECTOR_SEARCH_TIMEOUT_SECONDS = 5.0


async def search_vertical(
    vertical: Literal["activities", "books", "articles"],
    query: str,
    k: int,
    trace_id: str,
    customer_uuid: str | None = None,
    timeout: float = VECTOR_SEARCH_TIMEOUT_SECONDS,
) -> tuple[str, list[dict], str | None]:
    """Search a single vertical with timeout.
    
    Args:
        vertical: Which vertical to search
        query: Search query text
        k: Number of results to return
        trace_id: Trace ID for logging
        customer_uuid: Optional customer UUID for filtering
        timeout: Timeout in seconds (default: 5s)
        
    Returns:
        (vertical_name, results, error_message)
        - vertical_name: "activities" | "books" | "articles"
        - results: List of product dicts (empty if failed)
        - error_message: None if success, error string if failed
    """
    search_func_map = {
        "activities": search_activities_direct,
        "books": search_books_direct,
        "articles": search_articles_direct,
    }
    
    search_func = search_func_map[vertical]
    
    logger.info("vertical_search_starting",
               vertical=vertical,
               trace_id=trace_id,
               timeout=timeout)
    
    try:
        # Run search in thread pool with timeout
        results = await asyncio.wait_for(
            asyncio.to_thread(
                search_func,
                query=query,
                trace_id=trace_id,
                max_results=k,
                # customer_uuid parameter will be added later for multi-tenant
            ),
            timeout=timeout
        )
        
        logger.info("vertical_search_completed",
                   vertical=vertical,
                   trace_id=trace_id,
                   results_count=len(results))
        
        return (vertical, results, None)
        
    except asyncio.TimeoutError:
        logger.warning("vertical_search_timeout",
                      vertical=vertical,
                      trace_id=trace_id,
                      timeout=timeout)
        return (vertical, [], f"Search timeout after {timeout}s")
        
    except Exception as e:
        logger.error("vertical_search_error",
                    vertical=vertical,
                    trace_id=trace_id,
                    error=str(e),
                    error_type=type(e).__name__,
                    exc_info=True)
        return (vertical, [], f"Search error: {str(e)}")


async def parallel_search_node(state: AgentState) -> dict:
    """Execute vector searches for all requested verticals in parallel.
    
    This is a deterministic node - it searches exactly the verticals
    specified by the user (state["verticals"]), not based on LLM decision.
    
    Architecture:
    - User controls which verticals to search (not LLM)
    - All searches run in parallel (asyncio.gather)
    - Each vertical has 5s timeout
    - Partial results allowed (if some verticals succeed)
    - Errors tracked per vertical
    
    Args:
        state: Current workflow state with verticals list
        
    Returns:
        dict with:
        - activities: list[dict]
        - books: list[dict]
        - articles: list[dict]
        - errors: dict[str, str]
        - status: "complete" | "partial"
    """
    trace_id = state["trace_id"]
    verticals = state["verticals"]
    intent = state.get("intent", "")
    
    logger.info("parallel_search_started",
               trace_id=trace_id,
               verticals=verticals,
               k=state["k"],
               has_intent=bool(intent))
    
    # Build search query from intent + article + question
    query = build_search_query(
        article=state["article"],
        question=state["question"],
        intent=intent,
    )
    
    logger.debug("search_query_built",
                trace_id=trace_id,
                query_length=len(query))
    
    # Launch parallel searches for all requested verticals
    tasks = [
        search_vertical(
            vertical=v,
            query=query,
            k=state["k"],
            trace_id=trace_id,
            customer_uuid=state.get("customer_uuid"),
            timeout=VECTOR_SEARCH_TIMEOUT_SECONDS,
        )
        for v in verticals
    ]
    
    # Execute all searches in parallel
    logger.info("launching_parallel_searches",
               trace_id=trace_id,
               num_verticals=len(tasks))
    
    results = await asyncio.gather(*tasks)
    
    # Aggregate results
    updates = {
        "activities": [],
        "books": [],
        "articles": [],
        "errors": {},
    }
    
    for vertical, data, error in results:
        updates[vertical] = data
        if error:
            updates["errors"][vertical] = error
            logger.warning("vertical_search_had_error",
                          vertical=vertical,
                          error=error,
                          trace_id=trace_id)
    
    # Determine overall status
    has_results = any(len(updates[v]) > 0 for v in verticals)
    has_errors = len(updates["errors"]) > 0
    
    if has_errors:
        updates["status"] = "partial"
    else:
        updates["status"] = "complete"
    
    # Count results
    total_found = sum(len(updates[v]) for v in verticals)
    
    logger.info("parallel_search_completed",
               trace_id=trace_id,
               activities_count=len(updates["activities"]),
               books_count=len(updates["books"]),
               articles_count=len(updates["articles"]),
               total_found=total_found,
               status=updates["status"],
               errors_count=len(updates["errors"]))
    
    return updates

