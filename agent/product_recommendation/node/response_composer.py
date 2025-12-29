"""Response composer node for LangGraph workflow.

Pure function that reads state and formats grouped results.
No external calls, deterministic output.
"""

import structlog

from agent.product_recommendation.schemas import AgentState, ComposeResponseOutput

logger = structlog.get_logger(__name__)


def compose_response_node(state: AgentState) -> ComposeResponseOutput:
    """Compose final grouped response from search results.
    
    This is a pure function that:
    1. Groups results by vertical
    2. Sorts by relevance_score within each vertical
    3. Takes top K per vertical
    4. Counts totals
    
    Architecture: Reads state, no external calls, deterministic.
    
    Args:
        state: Current workflow state with search results
        
    Returns:
        dict with:
        - grouped_results: {vertical: [top_K_products]}
        - total_products: int (sum across all verticals)
    """
    trace_id = state.trace_id
    verticals = state.verticals
    k = state.k
    
    logger.info("composing_response",
               trace_id=trace_id,
               verticals=verticals,
               k=k)
    
    # Group results by vertical
    grouped_results = {}
    
    for vertical in verticals:
        # Get products for this vertical (may be empty)
        products = getattr(state, vertical, [])
        
        logger.debug("processing_vertical",
                    vertical=vertical,
                    products_count=len(products),
                    trace_id=trace_id)
        
        # Sort by relevance score (descending)
        sorted_products = sorted(
            products,
            key=lambda x: x.get("relevance_score", 0.0),
            reverse=True
        )
        
        # Take top K
        top_k = sorted_products[:k]
        grouped_results[vertical] = top_k
        
        logger.debug("vertical_processed",
                    vertical=vertical,
                    total_products=len(products),
                    top_k_selected=len(top_k),
                    trace_id=trace_id)
    
    # Count total products across all verticals
    total_products = sum(len(products) for products in grouped_results.values())
    
    logger.info("response_composed",
               trace_id=trace_id,
               total_products=total_products,
               verticals_with_results=[v for v, p in grouped_results.items() if p],
               status=state.status)
    
    # Return validated Pydantic model directly (type-safe)
    return ComposeResponseOutput(
        grouped_results=grouped_results,
        total_products=total_products,
    )

