"""Product vector search repository.

Repository for product-specific vector search operations.
Wraps generic VectorSearchClient and adds product-specific business logic:
- Column selection per product type
- Result parsing and transformation
- ProductResult construction
"""

from typing import Literal

from pydantic import ValidationError

from agent_will_smith.infra.vector_search_client import VectorSearchClient
from agent_will_smith.agent.product_recommendation.model.product import ProductResult
from agent_will_smith.agent.product_recommendation.repo.dto import (
    ActivityDTO,
    BookDTO,
    ArticleDTO,
)
from agent_will_smith.agent.product_recommendation.config import ProductRecommendationAgentConfig
from agent_will_smith.core.exceptions import UpstreamError
import structlog


class ProductVectorRepository:
    """Repository for product-specific vector search operations.

    Wraps generic VectorSearchClient and adds product-specific logic.
    Contains all product-specific transformations that were previously
    in the agent's VectorSearchClient.

    The repository layer is the boundary between:
    - Generic infrastructure (VectorSearchClient)
    - Domain/business logic (product types, DTOs, transformations)
    """

    def __init__(
        self,
        vector_client: VectorSearchClient,
        config: ProductRecommendationAgentConfig,
    ):
        """Initialize with injected dependencies.

        Args:
            vector_client: Generic vector search client
            config: Agent configuration with index names
        """
        self.vector_client = vector_client
        self.config = config
        self.logger = structlog.get_logger(__name__)

    def search_activities(
        self,
        query: str,
        max_results: int,
        customer_uuid: str | None = None,
    ) -> list[ProductResult]:
        """Search activities with product-specific logic.

        Args:
            query: Search query text
            max_results: Maximum number of results
            customer_uuid: Optional customer UUID for filtering

        Returns:
            List of ProductResult objects for activities
        """
        return self._search_products(
            query=query,
            index_name=self.config.activities_index,
            product_type="activity",
            max_results=max_results,
            customer_uuid=customer_uuid,
        )

    def search_books(
        self,
        query: str,
        max_results: int,
        customer_uuid: str | None = None,
    ) -> list[ProductResult]:
        """Search books with product-specific logic.

        Args:
            query: Search query text
            max_results: Maximum number of results
            customer_uuid: Optional customer UUID for filtering

        Returns:
            List of ProductResult objects for books
        """
        return self._search_products(
            query=query,
            index_name=self.config.books_index,
            product_type="book",
            max_results=max_results,
            customer_uuid=customer_uuid,
        )

    def search_articles(
        self,
        query: str,
        max_results: int,
        customer_uuid: str | None = None,
    ) -> list[ProductResult]:
        """Search articles with product-specific logic.

        Args:
            query: Search query text
            max_results: Maximum number of results
            customer_uuid: Optional customer UUID for filtering

        Returns:
            List of ProductResult objects for articles
        """
        return self._search_products(
            query=query,
            index_name=self.config.articles_index,
            product_type="article",
            max_results=max_results,
            customer_uuid=customer_uuid,
        )

    def _search_products(
        self,
        query: str,
        index_name: str,
        product_type: Literal["activity", "book", "article"],
        max_results: int,
        customer_uuid: str | None = None,
    ) -> list[ProductResult]:
        """Execute search with product-specific transformation.

        Args:
            query: Search query text
            index_name: Name of the vector search index
            product_type: Type of product being searched
            max_results: Maximum number of results
            customer_uuid: Optional customer UUID for filtering

        Returns:
            List of ProductResult objects
        """
        # Get product-specific columns
        columns = self._get_columns_for_product_type(product_type)

        # Build filters for multi-tenant isolation
        filters = {}
        if customer_uuid:
            filters["customer_uuid"] = customer_uuid

        # Call generic client
        raw_results = self.vector_client.similarity_search(
            index_name=index_name,
            query_text=query,
            columns=columns,
            num_results=max_results,
            filters=filters or None,
        )

        # Parse and transform to ProductResult
        return self._parse_results(raw_results, product_type, columns)

    def _get_columns_for_product_type(
        self, product_type: Literal["activity", "book", "article"]
    ) -> list[str]:
        """Get columns to fetch based on product type.

        PRODUCT-SPECIFIC LOGIC - stays in repository layer.

        Args:
            product_type: Type of product

        Returns:
            List of column names to retrieve
        """
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
        """Parse raw results into ProductResult objects.

        PRODUCT-SPECIFIC LOGIC - stays in repository layer.

        Args:
            results: Raw dict from Databricks Vector Search
            product_type: Type of product
            columns: List of column names fetched

        Returns:
            List of ProductResult objects
        """
        products = []

        if not isinstance(results, dict):
            self.logger.error("unexpected response type", response_type=type(results).__name__)
            raise UpstreamError(
                "Unexpected vector search response format",
                details={
                    "provider": "databricks_vector_search",
                    "operation": "parse_results",
                    "expected_type": "dict",
                    "actual_type": type(results).__name__,
                }
            )

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

            # Product-specific parsing
            product = self._parse_result_row(result_dict, product_type)
            products.append(product)

        return products

    def _parse_result_row(
        self, result_dict: dict, product_type: Literal["activity", "book", "article"]
    ) -> ProductResult:
        """Parse a single result row into ProductResult.

        PRODUCT-SPECIFIC LOGIC - stays in repository layer.

        Args:
            result_dict: Raw result dict
            product_type: Type of product

        Returns:
            ProductResult object
        """
        if product_type == "activity":
            try:
                dto = ActivityDTO.model_validate(result_dict)
            except ValidationError as e:
                raise UpstreamError(
                    "Invalid data format from vector search",
                    details={
                        "provider": "databricks_vector_search",
                        "operation": "parse_result",
                        "product_type": product_type,
                        "validation_errors": e.errors(),
                    }
                ) from e
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
            try:
                dto = BookDTO.model_validate(result_dict)
            except ValidationError as e:
                raise UpstreamError(
                    "Invalid data format from vector search",
                    details={
                        "provider": "databricks_vector_search",
                        "operation": "parse_result",
                        "product_type": product_type,
                        "validation_errors": e.errors(),
                    }
                ) from e
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
            try:
                dto = ArticleDTO.model_validate(result_dict)
            except ValidationError as e:
                raise UpstreamError(
                    "Invalid data format from vector search",
                    details={
                        "provider": "databricks_vector_search",
                        "operation": "parse_result",
                        "product_type": product_type,
                        "validation_errors": e.errors(),
                    }
                ) from e
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
