"""Parallel vector search node for LangGraph workflow.

Searches all requested verticals in parallel with timeout handling.

Namespace Architecture:
- Reads from: state.inputs, state.intent_node
- Writes to: state.search_node (results, status, errors)
"""

import asyncio
import structlog
from typing import Optional, Literal

from agent_will_smith.agent.product_recommendation.schemas.types import VERTICALS
from agent_will_smith.agent.product_recommendation.schemas.state import AgentState, SearchNodeNamespace
from agent_will_smith.agent.product_recommendation.schemas.messages import ProductResult
from agent_will_smith.agent.product_recommendation.repo.product_vector_repository import ProductVectorRepository
from agent_will_smith.agent.product_recommendation.config import ProductRecommendationAgentConfig


class ParallelSearchNode:
    """Node that searches all verticals in parallel.

    Injectable class following the joke_agent pattern.
    """

    # Constants for query building
    ARTICLE_EXCERPT_LENGTH = 300

    def __init__(
        self,
        product_repo: ProductVectorRepository,
        agent_config: ProductRecommendationAgentConfig,
    ):
        """Initialize with injected dependencies.

        Args:
            product_repo: Product vector repository for making searches
            agent_config: Agent configuration for index names and timeouts
        """
        self.product_repo = product_repo
        self.agent_config = agent_config
        self.logger = structlog.get_logger(__name__)

    def _build_search_query(
        self,
        article: str,
        question: str,
        intent: Optional[str] = None
    ) -> str:
        """Build search query deterministically from inputs.

        This method combines article, question, and intent into a search query
        without calling any LLM. The strategy is simple concatenation with structure.

        Args:
            article: Original article text
            question: User's question
            intent: Optional intent from LLM analysis

        Returns:
            Constructed search query string

        Note: This is deterministic - same inputs always produce same output.
        """
        # Use first N chars of article as context (avoid token limits)
        article_context = article[:self.ARTICLE_EXCERPT_LENGTH]
        if len(article) > self.ARTICLE_EXCERPT_LENGTH:
            article_context += "..."

        # Build query with clear structure
        query_parts = []

        # Intent comes first (most important for semantic search)
        if intent:
            query_parts.append(f"Intent: {intent}")

        # Question (what user is looking for)
        query_parts.append(f"Question: {question}")

        # Article context (background information)
        query_parts.append(f"Context: {article_context}")

        query = "\n\n".join(query_parts)

        self.logger.debug(
            "query built",
            query_length=len(query),
            has_intent=bool(intent),
            article_length=len(article)
        )

        return query

    def _aggregate_results(
        self,
        verticals: list[VERTICALS],
        results: list[list[ProductResult] | Exception]
    ) -> tuple[dict[VERTICALS, list[ProductResult]], dict[str, str], Literal["complete", "partial"]]:
        """Aggregate parallel search results and errors.

        Args:
            verticals: List of vertical names that were searched
            results: Results from asyncio.gather (list[ProductResult] or Exception)

        Returns:
            Tuple of (vertical_results, errors, status)
            - vertical_results: Dict mapping vertical name to list of ProductResult
            - errors: Dict mapping vertical name to error message
            - status: "complete" or "partial"
        """
        vertical_results: dict[VERTICALS, list[ProductResult]] = {}
        errors: dict[str, str] = {}

        for vertical, result in zip(verticals, results):
            if isinstance(result, Exception):
                self.logger.error(
                    "vertical search failed",
                    vertical=vertical,
                    error=str(result),
                    error_type=type(result).__name__,
                    exc_info=result,
                )
                errors[vertical] = f"{type(result).__name__}: {str(result)}"
                vertical_results[vertical] = []
            else:
                # result is list[ProductResult] - keep as Pydantic objects
                vertical_results[vertical] = result

        status: Literal["complete", "partial"] = "partial" if errors else "complete"

        return vertical_results, errors, status

    async def __call__(self, state: AgentState) -> dict:
        """Execute parallel vector searches for all requested verticals.

        PARTIAL FAILURE HANDLING (CODE_GUIDELINES.md Rule 2, Case 2):
        This method implements explicit partial failure handling. Individual
        vertical searches may fail (timeout, upstream errors), but failures
        are caught by asyncio.gather() and returned in the errors dict.
        Available results are still returned.

        Business Justification: Product recommendations should return available
        results even if some verticals fail. A book search failure shouldn't
        block activity or article results.

        Args:
            state: Current workflow state (Pydantic model with namespaces)

        Returns:
            dict with "search_node" key containing SearchNodeNamespace

        Raises:
            ValueError: If intent_node is None (dependency validation)
        """
        # Validate dependencies
        if state.intent_node is None:
            raise ValueError("intent_node must be set before search_node")

        # Read from namespaces
        verticals = state.inputs.verticals
        k = state.inputs.k
        customer_uuid = state.inputs.customer_uuid
        article = state.inputs.article
        question = state.inputs.question
        intent = state.intent_node.intent

        self.logger.info(
            "parallel search started",
            verticals=verticals,
            k=k,
            has_intent=bool(intent),
        )

        # Build search query from intent + article + question
        query = self._build_search_query(
            article=article,
            question=question,
            intent=intent,
        )

        self.logger.debug("search query built", query_length=len(query))

        # Launch parallel searches for all requested verticals
        tasks = [
            self._search_vertical(
                vertical=v,
                query=query,
                k=k,
                customer_uuid=customer_uuid,
            )
            for v in verticals
        ]

        self.logger.info("launching parallel searches", num_verticals=len(tasks))

        # Execute all searches in parallel
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Aggregate results
        vertical_results, errors, status = self._aggregate_results(verticals, results)

        # Count results
        total_found = sum(len(vertical_results.get(v, [])) for v in verticals)

        self.logger.info(
            "parallel search completed",
            vertical_results_keys=list(vertical_results.keys()),
            total_found=total_found,
            status=status,
            errors_count=len(errors),
        )

        # Write to own namespace (keep ProductResult objects!)
        return {
            "search_node": SearchNodeNamespace(
                results=vertical_results,
                status=status,
                errors=errors,
            )
        }

    async def _search_vertical(
        self,
        vertical: VERTICALS,
        query: str,
        k: int,
        customer_uuid: Optional[str] = None,
        timeout: Optional[float] = None,
    ) -> list[ProductResult]:
        """Search a single vertical with timeout.

        Args:
            vertical: Which vertical to search
            query: Search query text
            k: Number of results to return
            customer_uuid: Optional customer UUID for filtering
            timeout: Timeout in seconds (default: from config)

        Returns:
            list[ProductResult] (Pydantic objects, not dicts)
        """
        # Use config value if timeout not explicitly provided
        if timeout is None:
            timeout = self.agent_config.vector_search_timeout_seconds

        search_methods = {
            "activities": self.product_repo.search_activities,
            "books": self.product_repo.search_books,
            "articles": self.product_repo.search_articles,
        }

        search_method = search_methods[vertical]

        self.logger.info("vertical search starting", vertical=vertical, timeout=timeout)

        # Run search in thread pool with timeout
        # Exceptions from infrastructure (UpstreamError) bubble up naturally
        product_results = await asyncio.wait_for(
            asyncio.to_thread(
                search_method,
                query=query,
                max_results=k,
                customer_uuid=customer_uuid,
            ),
            timeout=timeout,
        )

        # Keep as Pydantic objects (no dict conversion!)
        self.logger.info(
            "vertical search completed",
            vertical=vertical,
            results_count=len(product_results),
        )

        return product_results
