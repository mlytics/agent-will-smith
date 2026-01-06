"""Vector search client for Databricks Vector Search.

Injectable client class for vector search with dependency injection support.
"""

from typing import Literal
from databricks.vector_search.client import VectorSearchClient as DatabricksVectorSearchClient
import structlog

from src.agent.product_recommendation.schemas import ProductResult, ActivityDTO, BookDTO, ArticleDTO
from src.core.exceptions import VectorSearchError


class VectorSearchClient:
    """Client class for vector search with dependency injection support.

    This replaces the global singleton pattern with an injectable class.
    The DI container manages the lifecycle as a singleton.
    """

    def __init__(
        self,
        workspace_url: str,
        client_id: str,
        client_secret: str,
        endpoint_name: str,
        logger: structlog.BoundLogger,
    ):
        """Initialize vector search client with configuration.

        Args:
            workspace_url: Databricks workspace URL
            client_id: Service principal client ID
            client_secret: Service principal client secret
            endpoint_name: Vector search endpoint name
            logger: Structlog logger with bound context
        """
        self.endpoint_name = endpoint_name
        self.logger = logger
        self._client = DatabricksVectorSearchClient(
            workspace_url=workspace_url,
            service_principal_client_id=client_id,
            service_principal_client_secret=client_secret,
            disable_notice=True,
        )
        self.logger.info("vector_search_client_initialized", endpoint=endpoint_name)

    def search_activities(
        self,
        query: str,
        index_name: str,
        max_results: int,
        customer_uuid: str | None = None,
    ) -> list[ProductResult]:
        """Search activities index.

        Args:
            query: Search query text
            index_name: Name of the activities index
            max_results: Maximum number of results
            customer_uuid: Optional customer UUID for filtering

        Returns:
            List of ProductResult objects
        """
        return self._search_index(query, index_name, max_results, "activity", customer_uuid)

    def search_books(
        self,
        query: str,
        index_name: str,
        max_results: int,
        customer_uuid: str | None = None,
    ) -> list[ProductResult]:
        """Search books index."""
        return self._search_index(query, index_name, max_results, "book", customer_uuid)

    def search_articles(
        self,
        query: str,
        index_name: str,
        max_results: int,
        customer_uuid: str | None = None,
    ) -> list[ProductResult]:
        """Search articles index."""
        return self._search_index(query, index_name, max_results, "article", customer_uuid)

    def _search_index(
        self,
        query_text: str,
        index_name: str,
        num_results: int,
        product_type: Literal["activity", "book", "article"],
        customer_uuid: str | None = None,
    ) -> list[ProductResult]:
        """Execute vector search query against a specific index.

        Args:
            query_text: Query text to search for
            index_name: Name of the vector search index
            num_results: Number of results to return
            product_type: Type of product being searched
            customer_uuid: Optional customer UUID for multi-tenant filtering

        Returns:
            List of ProductResult objects
        """
        self.logger.info(
            "vector_search_starting",
            index_name=index_name,
            product_type=product_type,
            query_length=len(query_text),
            num_results=num_results,
            customer_uuid=customer_uuid,
        )

        try:
            # Get vector search index
            index = self._client.get_index(endpoint_name=self.endpoint_name, index_name=index_name)

            # Define columns to fetch based on product type
            columns = self._get_columns_for_product_type(product_type)

            # Build filters for multi-tenant isolation
            filters = {}
            if customer_uuid:
                filters["customer_uuid"] = customer_uuid

            # Execute similarity search
            if filters:
                results = index.similarity_search(
                    query_text=query_text,
                    columns=columns,
                    filters=filters,
                    num_results=num_results,
                )
            else:
                results = index.similarity_search(
                    query_text=query_text,
                    columns=columns,
                    num_results=num_results,
                )

            # Parse response
            products = self._parse_results(results, product_type, columns)

            self.logger.info(
                "vector_search_completed",
                index_name=index_name,
                product_type=product_type,
                results_count=len(products),
            )

            return products

        except Exception as e:
            self.logger.error(
                "vector_search_failed",
                index_name=index_name,
                product_type=product_type,
                error=str(e),
                exc_info=True,
            )
            raise VectorSearchError(
                f"Vector search failed for {product_type} in {index_name}: {str(e)}"
            ) from e

    def _get_columns_for_product_type(
        self, product_type: Literal["activity", "book", "article"]
    ) -> list[str]:
        """Get columns to fetch based on product type."""
        if product_type == "activity":
            return [
                "content_id",
                "title",
                "description",
                "category",
                "location_name",
                "location_address",
                "organizer",
                "start_time",
                "end_time",
                "permalink_url",
                "cover_image_urls",
            ]
        elif product_type == "book":
            return [
                "content_id",
                "title_main",
                "title_subtitle",
                "description",
                "authors",
                "categories",
                "permalink_url",
                "cover_image_url",
                "prices",
            ]
        else:  # article
            return [
                "content_id",
                "title",
                "content",
                "authors",
                "keywords",
                "categories",
                "permalink_url",
                "thumbnail_url",
                "main_image_url",
                "publish_time",
            ]

    def _parse_results(
        self,
        results: dict,
        product_type: Literal["activity", "book", "article"],
        columns: list[str],
    ) -> list[ProductResult]:
        """Parse vector search results into ProductResult objects."""
        products = []

        if not isinstance(results, dict):
            self.logger.error("unexpected_response_type", response_type=type(results).__name__)
            raise VectorSearchError(f"Unexpected response type: {type(results).__name__}")

        result_data = results.get("result", {})
        data_array = result_data.get("data_array", [])
        manifest = result_data.get("manifest", {})

        # Get column names from manifest
        column_info = manifest.get("columns", [])
        if column_info:
            column_names = [
                col.get("name") if isinstance(col, dict) else col for col in column_info
            ]
        else:
            column_names = columns

        for row_data in data_array:
            try:
                if isinstance(row_data, list):
                    # Extract score (last element) if present
                    if len(row_data) > len(column_names):
                        score = row_data[-1]
                        data_values = row_data[:-1]
                    else:
                        score = 0.0
                        data_values = row_data
                    result_dict = dict(zip(column_names, data_values))
                    result_dict["score"] = score
                elif isinstance(row_data, dict):
                    result_dict = row_data
                else:
                    continue

                product = self._parse_result_row(result_dict, product_type)
                products.append(product)

            except Exception as e:
                self.logger.error("failed_to_parse_row", error=str(e), exc_info=True)
                continue

        return products

    def _parse_result_row(
        self, result_dict: dict, product_type: Literal["activity", "book", "article"]
    ) -> ProductResult:
        """Parse a single result row into ProductResult."""
        if product_type == "activity":
            dto = ActivityDTO.model_validate(result_dict)
            return ProductResult(
                product_id=dto.content_id,
                product_type="activity",
                title=dto.title,
                description=dto.description,
                relevance_score=dto.score,
                metadata={
                    "category": dto.category,
                    "location_name": dto.location_name,
                    "location_address": dto.location_address,
                    "organizer": dto.organizer,
                    "start_time": dto.start_time,
                    "end_time": dto.end_time,
                    "permalink_url": dto.permalink_url,
                    "cover_image_urls": dto.cover_image_urls,
                },
            )
        elif product_type == "book":
            dto = BookDTO.model_validate(result_dict)
            return ProductResult(
                product_id=dto.content_id,
                product_type="book",
                title=dto.title_main,
                description=dto.description,
                relevance_score=dto.score,
                metadata={
                    "subtitle": dto.title_subtitle,
                    "authors": dto.authors,
                    "categories": dto.categories,
                    "permalink_url": dto.permalink_url,
                    "cover_image_url": dto.cover_image_url,
                    "prices": dto.prices,
                },
            )
        else:  # article
            dto = ArticleDTO.model_validate(result_dict)
            return ProductResult(
                product_id=dto.content_id,
                product_type="article",
                title=dto.title,
                description=dto.content,
                relevance_score=dto.score,
                metadata={
                    "authors": dto.authors,
                    "keywords": dto.keywords,
                    "categories": dto.categories,
                    "permalink_url": dto.permalink_url,
                    "thumbnail_url": dto.thumbnail_url,
                    "main_image_url": dto.main_image_url,
                    "publish_time": dto.publish_time,
                },
            )
