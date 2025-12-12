"""Vector search tools for Databricks Vector Search.

Follows guidelines:
- "Tools must be deterministic at the interface level"
- "Tools return structured data, not English"
- "Tools should be small and single-purpose"
- "Tools are capabilities; orchestration decides sequence"
"""

from typing import Literal
from langchain.tools import tool, ToolRuntime
from databricks.vector_search.client import VectorSearchClient

from app.config import settings
from agent.schemas import AgentContext, ProductResult
import structlog

logger = structlog.get_logger(__name__)


def _create_vector_search_client() -> VectorSearchClient:
    """Create Databricks vector search client.

    Returns:
        Configured VectorSearchClient instance
    """
    return VectorSearchClient(disable_notice=True)


def _search_vector_index(
    client: VectorSearchClient,
    index_name: str,
    query_text: str,
    num_results: int,
    product_type: Literal["activity", "book"],
) -> list[ProductResult]:
    """Execute vector search query against a specific index.

    Args:
        client: Vector search client
        index_name: Name of the vector search index
        query_text: Query text to search for
        num_results: Number of results to return
        product_type: Type of product being searched

    Returns:
        List of ProductResult objects

    Note: This is a pure function - no side effects, deterministic output structure.
    """
    try:
        # Get vector search index
        index = client.get_index(endpoint_name=settings.vector_search_endpoint, index_name=index_name)

        # Execute similarity search
        results = index.similarity_search(
            query_text=query_text,
            columns=[
                "title",
                "description",
                "category",
                "location_name",
                "organizer",
                "author",
                "publisher",
            ],
            num_results=num_results,
        )

        # Transform to structured output
        products = []
        for result in results.get("result", {}).get("data_array", []):
            # Extract fields based on product type
            if product_type == "activity":
                product_id = result.get("event_id", "unknown")
                title = result.get("title", "Untitled Activity")
                description = result.get("description", None)
                metadata = {
                    "category": result.get("category"),
                    "location_name": result.get("location_name"),
                    "location_address": result.get("location_address"),
                    "organizer": result.get("organizer"),
                    "start_time": result.get("start_time"),
                    "end_time": result.get("end_time"),
                    "permalink": result.get("permalink"),
                }
            else:  # book
                product_id = result.get("item_id", "unknown")
                title = result.get("title_main", "Untitled Book")
                description = result.get("description", None)
                metadata = {
                    "subtitle": result.get("title_subtitle"),
                    "authors": result.get("author", []),
                    "publisher": result.get("publisher"),
                    "subjects": result.get("subject", []),
                    "permalink": result.get("permalink"),
                }

            # Get relevance score from vector search result
            relevance_score = result.get("score", 0.0)

            products.append(
                ProductResult(
                    product_id=product_id,
                    product_type=product_type,
                    title=title,
                    description=description,
                    relevance_score=relevance_score,
                    metadata=metadata,
                )
            )

        logger.info(
            "vector_search_completed",
            index_name=index_name,
            product_type=product_type,
            results_count=len(products),
        )

        return products

    except Exception as e:
        # Explicit error handling (guideline: "Have an explicit tool error strategy")
        logger.error(
            "vector_search_failed",
            index_name=index_name,
            product_type=product_type,
            error=str(e),
            exc_info=True,
        )
        # Return empty list rather than raising - agent can handle missing results
        return []


@tool
def search_activities(
    query: str, runtime: ToolRuntime[AgentContext]
) -> list[dict]:
    """Search for relevant activities based on the article and question.

    This tool performs semantic search in the activities vector index
    to find events and activities that match the user's interests.

    Args:
        query: Search query text (combine article context + question)
        runtime: Tool runtime with agent context

    Returns:
        List of activity results as dictionaries (for LLM consumption)
    """
    client = _create_vector_search_client()
    context = runtime.context

    # Use the configured k value, capped at max
    num_results = min(context.max_k, settings.max_k_products)

    logger.info(
        "searching_activities",
        trace_id=context.trace_id,
        query_length=len(query),
        num_results=num_results,
    )

    results = _search_vector_index(
        client=client,
        index_name=settings.activities_index,
        query_text=query,
        num_results=num_results,
        product_type="activity",
    )

    # Convert to dict for LLM (tools return JSON-serializable data)
    return [
        {
            "product_id": r.product_id,
            "product_type": r.product_type,
            "title": r.title,
            "description": r.description,
            "relevance_score": r.relevance_score,
            "metadata": r.metadata,
        }
        for r in results
    ]


@tool
def search_books(
    query: str, runtime: ToolRuntime[AgentContext]
) -> list[dict]:
    """Search for relevant books based on the article and question.

    This tool performs semantic search in the books vector index
    to find books that match the user's interests.

    Args:
        query: Search query text (combine article context + question)
        runtime: Tool runtime with agent context

    Returns:
        List of book results as dictionaries (for LLM consumption)
    """
    client = _create_vector_search_client()
    context = runtime.context

    # Use the configured k value, capped at max
    num_results = min(context.max_k, settings.max_k_products)

    logger.info(
        "searching_books",
        trace_id=context.trace_id,
        query_length=len(query),
        num_results=num_results,
    )

    results = _search_vector_index(
        client=client,
        index_name=settings.books_index,
        query_text=query,
        num_results=num_results,
        product_type="book",
    )

    # Convert to dict for LLM (tools return JSON-serializable data)
    return [
        {
            "product_id": r.product_id,
            "product_type": r.product_type,
            "title": r.title,
            "description": r.description,
            "relevance_score": r.relevance_score,
            "metadata": r.metadata,
        }
        for r in results
    ]

