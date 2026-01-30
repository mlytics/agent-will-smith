"""Output node that creates AgentOutput DTO."""

import structlog
import mlflow

from agent_will_smith.agent.product_recommendation.state import AgentState, AgentOutput
from agent_will_smith.agent.product_recommendation.model.product import ProductResult
from agent_will_smith.agent.product_recommendation.model.types import Vertical
from agent_will_smith.core.exceptions import AgentStateError


class OutputNode:
    """Transforms search results into AgentOutput DTO."""

    def __init__(self):
        self.logger = structlog.get_logger(__name__)

    @mlflow.trace(name="output_node")
    def __call__(self, state: AgentState) -> dict:
        """Create AgentOutput DTO from state namespaces.
        
        Sorts results by relevance, takes top K per vertical, and converts
        ProductResult objects to dicts.
        """
        if state.search_node is None:
            raise AgentStateError(
                "Invalid node execution order: search_node missing",
                details={
                    "current_node": "output_node",
                    "missing_dependency": "search_node",
                    "available_namespaces": [k for k, v in state.model_dump(exclude_none=True).items() if v is not None],
                },
                conflict=False,  # Programming error
            )
        if state.intent_node is None:
            raise AgentStateError(
                "Invalid node execution order: intent_node missing",
                details={
                    "current_node": "output_node",
                    "missing_dependency": "intent_node",
                    "available_namespaces": [k for k, v in state.model_dump(exclude_none=True).items() if v is not None],
                },
                conflict=False,  # Programming error
            )

        verticals = state.input.verticals
        k = state.input.k
        search_results = state.search_node.results

        self.logger.info("composing output DTO", verticals=verticals, k=k)

        grouped_results_pydantic: dict[Vertical, list[ProductResult]] = {}

        for vertical in verticals:
            products = search_results.get(vertical, [])

            self.logger.debug(
                "processing vertical",
                vertical=vertical,
                products_count=len(products),
            )

            sorted_products = sorted(
                products,
                key=lambda p: p.relevance_score,
                reverse=True
            )

            top_k = sorted_products[:k]
            grouped_results_pydantic[vertical] = top_k

            self.logger.debug(
                "vertical processed",
                vertical=vertical,
                total_products=len(products),
                top_k_selected=len(top_k),
            )

        grouped_results_dict = {
            vertical: [p.model_dump() for p in products]
            for vertical, products in grouped_results_pydantic.items()
        }

        total_products = sum(len(p) for p in grouped_results_pydantic.values())

        self.logger.info(
            "output DTO composed",
            total_products=total_products,
            verticals_with_results=[v for v, p in grouped_results_pydantic.items() if p],
        )

        return {
            "output": AgentOutput(
                grouped_results=grouped_results_dict,
                total_products=total_products,
                status=state.search_node.status,
                errors=state.search_node.errors,
                intent=state.intent_node.intent,
            )
        }
