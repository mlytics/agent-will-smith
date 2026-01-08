"""Output node that creates AgentOutput DTO.

This node is SPECIAL:
- Reads from: state.input, state.intent_node, state.search_node
- Writes to: state.output (AgentOutput DTO directly!)
- Combines: compose logic + ProductResult → dict conversion

Namespace Architecture:
- This is the ONLY node that writes a DTO (not an internal model) to state
- This is the ONLY place in the codebase where ProductResult → dict conversion happens
"""

import structlog

from agent_will_smith.agent.product_recommendation.schemas.state import AgentState
from agent_will_smith.agent.product_recommendation.schemas.messages import AgentOutput, ProductResult
from agent_will_smith.agent.product_recommendation.schemas.types import VERTICALS


class OutputNode:
    """Output node that writes AgentOutput DTO to state.output.

    Injectable class following the joke_agent pattern.
    This node has no external dependencies - pure transformation logic.
    """

    def __init__(self):
        """Initialize output node."""
        self.logger = structlog.get_logger(__name__)

    def __call__(self, state: AgentState) -> dict:
        """Create AgentOutput DTO from state namespaces.

        This node:
        1. Groups results by vertical
        2. Sorts by relevance_score within each vertical
        3. Takes top K per vertical
        4. Converts ProductResult objects → dict
        5. Assembles final AgentOutput DTO

        Args:
            state: Current workflow state (Pydantic model with namespaces)

        Returns:
            dict with "output" key containing AgentOutput DTO

        Raises:
            ValueError: If required namespaces are None (dependency validation)
        """
        # Validate dependencies
        if state.search_node is None:
            raise ValueError("search_node must be set before output")
        if state.intent_node is None:
            raise ValueError("intent_node must be set before output")

        # Read from namespaces (note: state.input is singular!)
        verticals = state.input.verticals
        k = state.input.k
        search_results = state.search_node.results

        self.logger.info("composing output DTO", verticals=verticals, k=k)

        # Compose logic: Sort and take top K per vertical
        grouped_results_pydantic: dict[VERTICALS, list[ProductResult]] = {}

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
            grouped_results_pydantic[vertical] = top_k

            self.logger.debug(
                "vertical processed",
                vertical=vertical,
                total_products=len(products),
                top_k_selected=len(top_k),
            )

        # Convert ProductResult → dict (ONLY conversion point in codebase!)
        grouped_results_dict = {
            vertical: [p.model_dump() for p in products]
            for vertical, products in grouped_results_pydantic.items()
        }

        # Count total products across all verticals
        total_products = sum(len(p) for p in grouped_results_pydantic.values())

        self.logger.info(
            "output DTO composed",
            total_products=total_products,
            verticals_with_results=[v for v, p in grouped_results_pydantic.items() if p],
        )

        # Write AgentOutput DTO to output namespace (SPECIAL!)
        return {
            "output": AgentOutput(
                grouped_results=grouped_results_dict,
                total_products=total_products,
                status=state.search_node.status,
                errors=state.search_node.errors,
                intent=state.intent_node.intent,
            )
        }
