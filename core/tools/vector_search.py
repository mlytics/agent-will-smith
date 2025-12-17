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


def _parse_result_row(result_dict: dict, product_type: Literal["activity", "book"]) -> ProductResult:
    """Parse a single result row from vector search into ProductResult.
    
    Args:
        result_dict: Dictionary with result data
        product_type: Type of product (activity or book)
        
    Returns:
        ProductResult object
    """
    if product_type == "activity":
        product_id = result_dict.get("event_id", "unknown")
        title = result_dict.get("title", "Untitled Activity")
        description = result_dict.get("description", None)
        metadata = {
            "category": result_dict.get("category"),
            "location_name": result_dict.get("location_name"),
            "location_address": result_dict.get("location_address"),
            "organizer": result_dict.get("organizer"),
            "start_time": result_dict.get("start_time"),
            "end_time": result_dict.get("end_time"),
            "permalink": result_dict.get("permalink"),
        }
    else:  # book
        product_id = result_dict.get("item_id", "unknown")
        title = result_dict.get("title_main", "Untitled Book")
        description = result_dict.get("description", None)
        metadata = {
            "subtitle": result_dict.get("title_subtitle"),
            "authors": result_dict.get("author", []),
            "publisher": result_dict.get("publisher"),
            "subjects": result_dict.get("subject", []),
            "permalink": result_dict.get("permalink"),
        }
    
    # Get relevance score
    relevance_score = result_dict.get("score", 0.0)
    
    return ProductResult(
        product_id=product_id,
        product_type=product_type,
        title=title,
        description=description,
        relevance_score=relevance_score,
        metadata=metadata,
    )


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
    logger.info("vector_search_starting",
               index_name=index_name,
               product_type=product_type,
               query_length=len(query_text),
               num_results=num_results,
               endpoint=settings.vector_search_endpoint)
    
    try:
        # Get vector search index
        logger.debug("getting_vector_index", index_name=index_name, endpoint=settings.vector_search_endpoint)
        index = client.get_index(endpoint_name=settings.vector_search_endpoint, index_name=index_name)
        logger.debug("vector_index_retrieved", index_name=index_name)

        # Define columns to fetch based on product type
        # CRITICAL: Must include primary key for product_id!
        if product_type == "activity":
            columns = [
                "event_id",  # ⭐ PRIMARY KEY - REQUIRED
                "title",
                "description",
                "category",
                "location_name",
                "location_address",
                "organizer",
                "start_time",
                "end_time",
                "permalink",
            ]
        else:  # book
            columns = [
                "item_id",  # ⭐ PRIMARY KEY - REQUIRED
                "title_main",
                "title_subtitle",
                "description",
                "author",
                "publisher",
                "subject",
                "permalink",
            ]

        # Execute similarity search
        results = index.similarity_search(
            query_text=query_text,
            columns=columns,
            num_results=num_results,
        )

        # Parse response - Databricks vector search returns specific format
        products = []
        
        if not isinstance(results, dict):
            logger.error("unexpected_response_type", response_type=type(results).__name__)
            return []
        
        # Get result data and manifest
        result_data = results.get("result", {})
        data_array = result_data.get("data_array", [])
        manifest = result_data.get("manifest", {})
        
        # Column info from manifest
        column_info = manifest.get("columns", [])
        if column_info:
            # Extract column names from manifest
            # Manifest format: [{"name": "col1"}, {"name": "col2"}, ...]
            column_names = [col.get("name") if isinstance(col, dict) else col 
                           for col in column_info]
        else:
            column_names = columns  # Fallback to requested columns
        
        logger.debug("vector_search_response_parsed",
                    data_array_length=len(data_array),
                    column_count=len(column_names),
                    data_type=type(data_array[0]).__name__ if data_array else "empty")
        
        # Log what we got back
        logger.info("vector_search_response_received",
                   index_name=index_name,
                   product_type=product_type,
                   data_array_count=len(data_array),
                   column_names_count=len(column_names))
        
        # Process each result row
        for idx, row_data in enumerate(data_array):
            # Check if row is a list (column values) or dict
            if isinstance(row_data, list):
                # Row is a list of values
                # CRITICAL: Last element is the similarity score (not in column_names)
                # Format: [col1, col2, ..., colN, score]
                if len(row_data) > len(column_names):
                    # Extract score (last element)
                    score = row_data[-1]
                    data_values = row_data[:-1]
                else:
                    score = 0.0
                    data_values = row_data
                
                # Map column values to names
                result_dict = dict(zip(column_names, data_values))
                result_dict["score"] = score  # Add score explicitly
                
                logger.debug("parsed_row_from_list", 
                           row_index=idx,
                           score=score,
                           result_dict_keys=list(result_dict.keys()))
            elif isinstance(row_data, dict):
                # Row is already a dict
                result_dict = row_data
                logger.debug("parsed_row_from_dict", result_dict_keys=list(result_dict.keys()))
            else:
                logger.warning("unexpected_row_format", row_type=type(row_data).__name__)
                continue
            
            # Parse into ProductResult
            try:
                product = _parse_result_row(result_dict, product_type)
                products.append(product)
                logger.info("product_parsed_successfully", 
                           product_id=product.product_id,
                           product_type=product_type,
                           title=product.title,
                           score=product.relevance_score)
            except Exception as e:
                logger.error("failed_to_parse_row", error=str(e), row_data=result_dict, exc_info=True)
                continue

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


def search_activities_direct(
    query: str,
    trace_id: str,
    max_results: int = 10,
) -> list[dict]:
    """Search for relevant activities (direct call, no ToolRuntime).

    This is the direct function for calling outside of agent frameworks.

    Args:
        query: Search query text
        trace_id: Trace ID for logging
        max_results: Maximum number of results to return

    Returns:
        List of activity results as dictionaries
    """
    client = _create_vector_search_client()
    num_results = min(max_results, settings.max_k_products)

    logger.info(
        "searching_activities",
        trace_id=trace_id,
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

    # Convert to dict
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
def search_activities(
    query: str, runtime: ToolRuntime[AgentContext]
) -> list[dict]:
    """Search for relevant activities (for agent framework use).

    This tool performs semantic search in the activities vector index.

    Args:
        query: Search query text
        runtime: Tool runtime with agent context

    Returns:
        List of activity results as dictionaries
    """
    context = runtime.context
    return search_activities_direct(
        query=query,
        trace_id=context.trace_id,
        max_results=context.max_k
    )


def search_books_direct(
    query: str,
    trace_id: str,
    max_results: int = 10,
) -> list[dict]:
    """Search for relevant books (direct call, no ToolRuntime).

    This is the direct function for calling outside of agent frameworks.

    Args:
        query: Search query text
        trace_id: Trace ID for logging
        max_results: Maximum number of results to return

    Returns:
        List of book results as dictionaries
    """
    client = _create_vector_search_client()
    num_results = min(max_results, settings.max_k_products)

    logger.info(
        "searching_books",
        trace_id=trace_id,
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

    # Convert to dict
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
    """Search for relevant books (for agent framework use).

    This tool performs semantic search in the books vector index.

    Args:
        query: Search query text
        runtime: Tool runtime with agent context

    Returns:
        List of book results as dictionaries
    """
    context = runtime.context
    return search_books_direct(
        query=query,
        trace_id=context.trace_id,
        max_results=context.max_k
    )

