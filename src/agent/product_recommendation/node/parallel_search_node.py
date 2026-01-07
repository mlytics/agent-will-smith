"""Parallel vector search node for LangGraph workflow.

Searches all requested verticals in parallel with timeout handling.
"""

import asyncio
import structlog

from src.agent.product_recommendation.constants import VERTICALS
from src.agent.product_recommendation.schemas import (
    AgentState,
    ParallelSearchOutput,
    VerticalSearchResult,
)
from src.agent.product_recommendation.node.query_builder import QueryBuilder
from src.agent.product_recommendation.infra.vector_search import VectorSearchClient
from src.agent.product_recommendation.config.settings import ProductRecommendationAgentConfig
from src.core.exceptions import UpstreamTimeoutError, UpstreamError

# Timeout per vertical search (5 seconds)
VECTOR_SEARCH_TIMEOUT_SECONDS = 5.0


class ParallelSearchNode:
    """Node that searches all verticals in parallel.

    Injectable class following the joke_agent pattern.
    """

    def __init__(
        self,
        vector_client: VectorSearchClient,
        query_builder: QueryBuilder,
        agent_config: ProductRecommendationAgentConfig,
    ):
        """Initialize with injected dependencies.

        Args:
            vector_client: Vector search client for making searches
            query_builder: Query builder for constructing search queries
            agent_config: Agent configuration for index names
        """
        self.vector_client = vector_client
        self.query_builder = query_builder
        self.agent_config = agent_config
        self.logger = structlog.get_logger(__name__)

    async def __call__(self, state: AgentState) -> ParallelSearchOutput:
        """Execute parallel vector searches for all requested verticals.

        Args:
            state: Current workflow state (Pydantic model)

        Returns:
            ParallelSearchOutput with results per vertical
        """
        verticals = state.verticals
        intent = state.intent or ""

        self.logger.info(
            "parallel_search_started",
            verticals=verticals,
            k=state.k,
            has_intent=bool(intent),
        )

        # Build search query from intent + article + question
        query = self.query_builder.build_search_query(
            article=state.article,
            question=state.question,
            intent=intent,
        )

        self.logger.debug("search_query_built", query_length=len(query))

        # Launch parallel searches for all requested verticals
        tasks = [
            self._search_vertical(
                vertical=v,
                query=query,
                k=state.k,
                customer_uuid=state.customer_uuid,
            )
            for v in verticals
        ]

        self.logger.info("launching_parallel_searches", num_verticals=len(tasks))

        # Execute all searches in parallel
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Aggregate results
        updates = {
            "activities": [],
            "books": [],
            "articles": [],
            "errors": {},
        }

        for i, result in enumerate(results):
            vertical = verticals[i]

            if isinstance(result, Exception):
                self.logger.error(
                    "vertical_search_failed",
                    vertical=vertical,
                    error=str(result),
                    error_type=type(result).__name__,
                    exc_info=result,
                )
                updates["errors"][vertical] = f"{type(result).__name__}: {str(result)}"
                updates[vertical] = []
            else:
                updates[vertical] = result.products
                if result.error:
                    updates["errors"][vertical] = result.error
                    self.logger.warning(
                        "vertical_search_had_error",
                        vertical=result.vertical,
                        error=result.error,
                    )

        # Determine overall status
        has_errors = len(updates["errors"]) > 0
        status = "partial" if has_errors else "complete"

        # Count results
        total_found = sum(len(updates[v]) for v in verticals)

        self.logger.info(
            "parallel_search_completed",
            activities_count=len(updates["activities"]),
            books_count=len(updates["books"]),
            articles_count=len(updates["articles"]),
            total_found=total_found,
            status=status,
            errors_count=len(updates["errors"]),
        )

        return ParallelSearchOutput(
            activities=updates["activities"],
            books=updates["books"],
            articles=updates["articles"],
            errors=updates["errors"],
            status=status,
        )

    async def _search_vertical(
        self,
        vertical: VERTICALS,
        query: str,
        k: int,
        customer_uuid: str | None = None,
        timeout: float = VECTOR_SEARCH_TIMEOUT_SECONDS,
    ) -> VerticalSearchResult:
        """Search a single vertical with timeout.

        Args:
            vertical: Which vertical to search
            query: Search query text
            k: Number of results to return
            customer_uuid: Optional customer UUID for filtering
            timeout: Timeout in seconds (default: 5s)

        Returns:
            VerticalSearchResult with products or error
        """
        search_methods = {
            "activities": (self.vector_client.search_activities, self.agent_config.activities_index),
            "books": (self.vector_client.search_books, self.agent_config.books_index),
            "articles": (self.vector_client.search_articles, self.agent_config.articles_index),
        }

        search_method, index_name = search_methods[vertical]

        self.logger.info("vertical_search_starting", vertical=vertical, timeout=timeout)

        try:
            # Run search in thread pool with timeout
            product_results = await asyncio.wait_for(
                asyncio.to_thread(
                    search_method,
                    query=query,
                    index_name=index_name,
                    max_results=k,
                    customer_uuid=customer_uuid,
                ),
                timeout=timeout,
            )

            # Convert Pydantic models to dicts for state storage
            results_dicts = [r.model_dump() for r in product_results]

            self.logger.info(
                "vertical_search_completed",
                vertical=vertical,
                results_count=len(results_dicts),
            )

            return VerticalSearchResult(vertical=vertical, products=results_dicts, error=None)

        except asyncio.TimeoutError as e:
            self.logger.warning(
                "vertical_search_timeout",
                vertical=vertical,
                timeout=timeout,
                exc_info=True,
            )
            raise UpstreamTimeoutError(
                f"Vector search timeout for {vertical}",
                details={
                    "provider": "databricks_vector_search",
                    "operation": "similarity_search",
                    "vertical": vertical,
                    "timeout_seconds": timeout,
                }
            ) from e

        except Exception as e:
            self.logger.error(
                "vertical_search_error",
                vertical=vertical,
                error=str(e),
                error_type=type(e).__name__,
                exc_info=True,
            )
            raise UpstreamError(
                f"Vector search failed for {vertical}",
                details={
                    "provider": "databricks_vector_search",
                    "operation": "similarity_search",
                    "vertical": vertical,
                    "error": str(e),
                }
            ) from e
