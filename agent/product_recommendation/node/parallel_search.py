"""Parallel vector search node for LangGraph workflow.

Searches all requested verticals in parallel with timeout handling.
Architecture: Deterministic function-based tools, no LLM decision-making.
"""

import asyncio
import structlog
from databricks.vector_search.client import VectorSearchClient

from agent.product_recommendation.constants import VERTICALS
from agent.product_recommendation.schemas import AgentState, ParallelSearchOutput, VerticalSearchResult
from agent.product_recommendation.node.query_builder import build_search_query
from agent.product_recommendation.infra.vector_search import (
    search_activities_direct,
    search_books_direct,
    search_articles_direct,
)

logger = structlog.get_logger(__name__)

# Timeout per vertical search (5 seconds)
VECTOR_SEARCH_TIMEOUT_SECONDS = 5.0


async def search_vertical(
    vertical: VERTICALS,
    query: str,
    k: int,
    trace_id: str,
    vector_client: VectorSearchClient,
    customer_uuid: str | None = None,
    timeout: float = VECTOR_SEARCH_TIMEOUT_SECONDS,
) -> VerticalSearchResult:
    """Search a single vertical with timeout.
    
    Args:
        vertical: Which vertical to search
        query: Search query text
        k: Number of results to return
        trace_id: Trace ID for logging
        vector_client: Injected VectorSearchClient from pool (DI)
        customer_uuid: Optional customer UUID for filtering
        timeout: Timeout in seconds (default: 5s)
        
    Returns:
        VerticalSearchResult (Pydantic model) with:
        - vertical: Literal type for which vertical
        - products: List of product dicts (empty if failed)
        - error: None if success, error string if failed
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
        # Returns list[ProductResult] (Pydantic models)
        # Pass REQUIRED injected vector_client from pool (DI enforced)
        product_results = await asyncio.wait_for(
            asyncio.to_thread(
                search_func,
                query=query,
                trace_id=trace_id,
                vector_client=vector_client,
                max_results=k,
                customer_uuid=customer_uuid,
            ),
            timeout=timeout
        )
        
        # Convert Pydantic models to dicts for state storage
        results_dicts = [r.model_dump() for r in product_results]
        
        logger.info("vertical_search_completed",
                   vertical=vertical,
                   trace_id=trace_id,
                   results_count=len(results_dicts))
        
        # Return validated Pydantic model
        return VerticalSearchResult(
            vertical=vertical,
            products=results_dicts,
            error=None
        )
        
    except asyncio.TimeoutError as e:
        # Timeout is expected behavior, log and raise with context
        logger.warning("vertical_search_timeout",
                      vertical=vertical,
                      trace_id=trace_id,
                      timeout=timeout,
                      exc_info=True)
        from core.exceptions import VectorSearchTimeout
        raise VectorSearchTimeout(
            f"Search timeout for {vertical} after {timeout}s (trace: {trace_id})"
        ) from e
        
    except Exception as e:
        # Unexpected error - fail fast with full context
        logger.error("vertical_search_error",
                    vertical=vertical,
                    trace_id=trace_id,
                    error=str(e),
                    error_type=type(e).__name__,
                    exc_info=True)  # Shows line number
        from core.exceptions import VectorSearchError
        raise VectorSearchError(
            f"Search failed for {vertical} (trace: {trace_id}): {str(e)}"
        ) from e  # Preserves stack trace with line numbers


async def parallel_search_node(
    state: AgentState,
    vector_client: VectorSearchClient,
) -> ParallelSearchOutput:
    """Execute vector searches for all requested verticals in parallel.
    
    This is a deterministic node - it searches exactly the verticals
    specified by the user (state.verticals), not based on LLM decision.
    
    Architecture:
    - User controls which verticals to search (not LLM)
    - All searches run in parallel (asyncio.gather)
    - Each vertical has 5s timeout
    - Partial results allowed (if some verticals succeed)
    - Errors tracked per vertical
    - Dependencies injected (vector_client) or retrieved from pool
    
    Args:
        state: Current workflow state with verticals list
        vector_client: Optional injected VectorSearchClient (DI)
        
    Returns:
        ParallelSearchOutput with:
        - activities: list[dict]
        - books: list[dict]
        - articles: list[dict]
        - errors: dict[str, str]
        - status: "complete" | "partial"
    """
    # Use injected vector client from pool (DI via functools.partial)
    logger.debug("vector_client_injected", 
                client_type=type(vector_client).__name__)
    
    trace_id = state.trace_id
    verticals = state.verticals
    intent = state.intent or ""
    
    logger.info("parallel_search_started",
               trace_id=trace_id,
               verticals=verticals,
               k=state.k,
               has_intent=bool(intent))
    
    # Build search query from intent + article + question
    query = build_search_query(
        article=state.article,
        question=state.question,
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
            k=state.k,
            trace_id=trace_id,
            vector_client=vector_client,
            customer_uuid=state.customer_uuid,
            timeout=VECTOR_SEARCH_TIMEOUT_SECONDS,
        )
        for v in verticals
    ]
    
    # Execute all searches in parallel
    # Use return_exceptions=True to catch failures without stopping other searches
    logger.info("launching_parallel_searches",
               trace_id=trace_id,
               num_verticals=len(tasks))
    
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Aggregate results - handle both successful results and exceptions
    updates = {
        "activities": [],
        "books": [],
        "articles": [],
        "errors": {},
    }
    
    for i, result in enumerate(results):
        vertical = verticals[i]
        
        if isinstance(result, Exception):
            # Search failed - log error with full context
            logger.error("vertical_search_failed",
                        vertical=vertical,
                        trace_id=trace_id,
                        error=str(result),
                        error_type=type(result).__name__,
                        exc_info=result)  # Shows line number where it failed
            updates["errors"][vertical] = f"{type(result).__name__}: {str(result)}"
            updates[vertical] = []
        else:
            # Search succeeded
            updates[vertical] = result.products
            if result.error:
                updates["errors"][vertical] = result.error
            logger.warning("vertical_search_had_error",
                              vertical=result.vertical,
                              error=result.error,
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
    
    # Return validated Pydantic model directly (type-safe)
    return ParallelSearchOutput(
        activities=updates["activities"],
        books=updates["books"],
        articles=updates["articles"],
        errors=updates["errors"],
        status=updates["status"],
    )

