"""Response composer node for LangGraph workflow.

Pure function that reads state and formats grouped results.
No external calls, deterministic output.

Namespace Architecture:
- Reads from: state.inputs, state.search_node
- Writes to: state.compose_node (grouped_results, total_products)
"""

import structlog

from agent_will_smith.agent.product_recommendation.schemas.state import AgentState, ComposeNodeNamespace
from agent_will_smith.agent.product_recommendation.schemas.types import VERTICALS
from agent_will_smith.agent.product_recommendation.schemas.messages import ProductResult


class ComposeResponseNode:
    """Node that composes final response from search results.

    Injectable class following the joke_agent pattern.
    This is a pure node with no external dependencies.
    """

    def __init__(self):
        """Initialize response composer."""
        self.logger = structlog.get_logger(__name__)

    def __call__(self, state: AgentState) -> dict:
        """Compose final grouped response from search results.

        This node:
        1. Groups results by vertical
        2. Sorts by relevance_score within each vertical
        3. Takes top K per vertical
        4. Counts totals

        Args:
            state: Current workflow state (Pydantic model with namespaces)

        Returns:
            dict with "compose_node" key containing ComposeNodeNamespace

        Raises:
            ValueError: If search_node is None (dependency validation)
        """
        # Validate dependencies
        if state.search_node is None:
            raise ValueError("search_node must be set before compose_node")

        # Read from namespaces
        verticals = state.inputs.verticals
        k = state.inputs.k
        search_results = state.search_node.results

        self.logger.info("composing response", verticals=verticals, k=k)

        # Group results by vertical and take top K
        grouped_results: dict[VERTICALS, list[ProductResult]] = {}

        for vertical in verticals:
            # Get products for this vertical (may be empty)
            products = search_results.get(vertical, [])

            self.logger.debug(
                "processing vertical",
                vertical=vertical,
                products_count=len(products),
            )

            # Sort by relevance score (type-safe Pydantic field access!)
            sorted_products = sorted(
                products,
                key=lambda p: p.relevance_score,  # ✅ No string keys needed
                reverse=True
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
        )

        # Write to own namespace
        return {
            "compose_node": ComposeNodeNamespace(
                grouped_results=grouped_results,
                total_products=total_products,
            )
        }
