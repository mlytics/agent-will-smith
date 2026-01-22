"""Parallel vector search node for LangGraph workflow."""

import asyncio
import structlog
from typing import Optional, Literal

from agent_will_smith.agent.product_recommendation.model.types import Vertical
from agent_will_smith.agent.product_recommendation.model.product import ProductResult
from agent_will_smith.agent.product_recommendation.model.namespaces import SearchNodeNamespace
from agent_will_smith.agent.product_recommendation.state import AgentState
from agent_will_smith.agent.product_recommendation.repo.product_vector_repository import ProductVectorRepository
from agent_will_smith.agent.product_recommendation.config import Config


class ParallelSearchNode:
    """Searches all verticals in parallel with timeout handling."""

    ARTICLE_EXCERPT_LENGTH = 300

    def __init__(
        self,
        product_repo: ProductVectorRepository,
        agent_config: Config,
    ):
        self.product_repo = product_repo
        self.agent_config = agent_config
        self.logger = structlog.get_logger(__name__)

    def _build_search_query(
        self,
        article: Optional[str],
        question: str,
        intent: Optional[str] = None
    ) -> str:
        """Build search query deterministically from inputs."""
        query_parts = []
        if intent:
            query_parts.append(f"Intent: {intent}")
        query_parts.append(f"Question: {question}")

        # Add article context if provided
        if article:
            article_context = article[:self.ARTICLE_EXCERPT_LENGTH]
            if len(article) > self.ARTICLE_EXCERPT_LENGTH:
                article_context += "..."
            query_parts.append(f"Context: {article_context}")

        query = "\n\n".join(query_parts)

        self.logger.debug(
            "query built",
            query_length=len(query),
            has_intent=bool(intent),
            article_length=len(article) if article else 0,
            has_article=bool(article),
        )

        return query

    def _aggregate_results(
        self,
        verticals: list[Vertical],
        results: list[list[ProductResult] | Exception]
    ) -> tuple[dict[Vertical, list[ProductResult]], dict[str, str], Literal["complete", "partial"]]:
        """Aggregate parallel search results and errors."""
        vertical_results: dict[Vertical, list[ProductResult]] = {}
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
                vertical_results[vertical] = result

        status: Literal["complete", "partial"] = "partial" if errors else "complete"

        return vertical_results, errors, status

    async def __call__(self, state: AgentState) -> dict:
        """Execute parallel vector searches for all requested verticals.
        
        Implements partial failure handling: individual vertical searches may fail,
        but available results are still returned.
        """
        if state.intent_node is None:
            raise ValueError("intent_node must be set before search_node")

        verticals = state.input.verticals
        k = state.input.k
        customer_uuid = state.input.customer_uuid
        article = state.input.article
        question = state.input.question
        intent = state.intent_node.intent

        self.logger.info(
            "parallel search started",
            verticals=verticals,
            k=k,
            has_intent=bool(intent),
        )

        query = self._build_search_query(
            article=article,
            question=question,
            intent=intent,
        )

        self.logger.debug("search query built", query_length=len(query))

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

        results = await asyncio.gather(*tasks, return_exceptions=True)

        vertical_results, errors, status = self._aggregate_results(verticals, results)

        total_found = sum(len(vertical_results.get(v, [])) for v in verticals)

        self.logger.info(
            "parallel search completed",
            vertical_results_keys=list(vertical_results.keys()),
            total_found=total_found,
            status=status,
            errors_count=len(errors),
        )

        return {
            "search_node": SearchNodeNamespace(
                results=vertical_results,
                status=status,
                errors=errors,
            )
        }

    async def _search_vertical(
        self,
        vertical: Vertical,
        query: str,
        k: int,
        customer_uuid: Optional[str] = None,
        timeout: Optional[float] = None,
    ) -> list[ProductResult]:
        """Search a single vertical with timeout.
        
        Now uses the generic repository.search() method.
        No more method mapping dictionary needed!
        """
        if timeout is None:
            timeout = self.agent_config.vector_search_timeout_seconds

        self.logger.info("vertical search starting", vertical=vertical, timeout=timeout)

        # Direct call to generic search method - no mapping needed!
        product_results = await asyncio.wait_for(
            asyncio.to_thread(
                self.product_repo.search,
                vertical=vertical,
                query=query,
                max_results=k,
                customer_uuid=customer_uuid,
            ),
            timeout=timeout,
        )

        self.logger.info(
            "vertical search completed",
            vertical=vertical,
            results_count=len(product_results),
        )

        return product_results
