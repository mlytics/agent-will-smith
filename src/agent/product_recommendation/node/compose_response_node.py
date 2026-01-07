"""Response composer node for LangGraph workflow.

Pure function that reads state and formats grouped results.
No external calls, deterministic output.
"""

import structlog

from src.agent.product_recommendation.schemas import AgentState, ComposeResponseOutput


class ComposeResponseNode:
    """Node that composes final response from search results.

    Injectable class following the joke_agent pattern.
    This is a pure node with no external dependencies.
    """

    def __init__(self):
        """Initialize response composer."""
        self.logger = structlog.get_logger(__name__)

    def __call__(self, state: AgentState) -> ComposeResponseOutput:
        """Compose final grouped response from search results.

        This node:
        1. Groups results by vertical
        2. Sorts by relevance_score within each vertical
        3. Takes top K per vertical
        4. Counts totals

        Args:
            state: Current workflow state (Pydantic model)

        Returns:
            ComposeResponseOutput with grouped results and totals
        """
        verticals = state.verticals
        k = state.k

        self.logger.info("composing response", verticals=verticals, k=k)

        # Group results by vertical
        grouped_results = {}

        for vertical in verticals:
            # Get products for this vertical (may be empty)
            products = getattr(state, vertical, [])

            self.logger.debug(
                "processing vertical",
                vertical=vertical,
                products_count=len(products),
            )

            # Sort by relevance score (descending)
            sorted_products = sorted(
                products, key=lambda x: x.get("relevance_score", 0.0), reverse=True
            )

            # Take top K
            top_k = sorted_products[:k]
            grouped_results[vertical] = top_k

            self.logger.debug(
                "vertical processed",
                vertical=vertical,
                total_products=len(products),
                top_k_selected=len(top_k),
            )

        # Count total products across all verticals
        total_products = sum(len(products) for products in grouped_results.values())

        self.logger.info(
            "response composed",
            total_products=total_products,
            verticals_with_results=[v for v, p in grouped_results.items() if p],
            status=state.status,
        )

        return ComposeResponseOutput(
            grouped_results=grouped_results,
            total_products=total_products,
        )
