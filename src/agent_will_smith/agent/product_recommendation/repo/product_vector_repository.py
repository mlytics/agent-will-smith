"""Product vector search repository.

Repository for product-specific vector search operations.
Wraps generic VectorSearchClient and adds product-specific business logic:
- Column selection per product type
- Result parsing and transformation
- ProductResult construction

Uses Product Registry for centralized configuration.
"""

from pydantic import ValidationError
import structlog

from agent_will_smith.infra.vector_search_client import VectorSearchClient
from agent_will_smith.agent.product_recommendation.model.product import ProductResult
from agent_will_smith.agent.product_recommendation.model.types import VERTICALS
from agent_will_smith.agent.product_recommendation.model.product_registry import get_product_config
from agent_will_smith.agent.product_recommendation.config import Config
from agent_will_smith.core.exceptions import UpstreamError


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
        config: Config,
    ):
        """Initialize with injected dependencies.

        Args:
            vector_client: Generic vector search client
            config: Agent configuration with index names
        """
        self.vector_client = vector_client
        self.config = config
        self.logger = structlog.get_logger(__name__)

    def search(
        self,
        vertical: VERTICALS,
        query: str,
        max_results: int,
        customer_uuid: str | None = None,
    ) -> list[ProductResult]:
        """Search a product vertical with product-specific logic.
        
        Generic method that works for all product types using the registry.
        Replaces search_activities(), search_books(), search_articles().
        
        Args:
            vertical: Product vertical to search ("activities", "books", "articles")
            query: Search query text
            max_results: Maximum number of results
            customer_uuid: Optional customer UUID for filtering
            
        Returns:
            List of ProductResult objects
            
        Example:
            >>> results = repo.search("activities", "hiking trails", max_results=10)
        """
        config = get_product_config(vertical)
        index_name = getattr(self.config, config.index_config_key)
        
        return self._search_products(
            query=query,
            index_name=index_name,
            vertical=vertical,
            max_results=max_results,
            customer_uuid=customer_uuid,
        )


    def _search_products(
        self,
        query: str,
        index_name: str,
        vertical: VERTICALS,
        max_results: int,
        customer_uuid: str | None = None,
    ) -> list[ProductResult]:
        """Execute search with product-specific transformation.

        Args:
            query: Search query text
            index_name: Name of the vector search index
            vertical: Product vertical being searched
            max_results: Maximum number of results
            customer_uuid: Optional customer UUID for filtering

        Returns:
            List of ProductResult objects
        """
        # Get product-specific columns from registry
        columns = self._get_columns_for_vertical(vertical)

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
        return self._parse_results(raw_results, vertical, columns)

    def _get_columns_for_vertical(self, vertical: VERTICALS) -> list[str]:
        """Get columns to fetch for a product vertical using registry.
        
        Args:
            vertical: Product vertical name
            
        Returns:
            List of column names to retrieve from vector search
        """
        return get_product_config(vertical).columns

    def _parse_results(
        self,
        results: dict,
        vertical: VERTICALS,
        columns: list[str],
    ) -> list[ProductResult]:
        """Parse raw results into ProductResult objects.

        Args:
            results: Raw dict from Databricks Vector Search
            vertical: Product vertical
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

            # Generic parsing using registry
            product = self._parse_result_row(result_dict, vertical)
            products.append(product)

        return products

    def _parse_result_row(
        self, result_dict: dict, vertical: VERTICALS
    ) -> ProductResult:
        """Parse a single result row into ProductResult using registry.
        
        Generic implementation that works for all product types.
        Uses ProductTypeConfig to drive DTO validation and field mapping.
        
        Args:
            result_dict: Raw result dict from vector search
            vertical: Product vertical name
            
        Returns:
            ProductResult object
            
        Raises:
            UpstreamError: If data validation fails
        """
        config = get_product_config(vertical)
        
        # Validate using product-specific DTO
        try:
            dto = config.dto_class.model_validate(result_dict)
        except ValidationError as e:
            raise UpstreamError(
                "Invalid data format from vector search",
                details={
                    "provider": "databricks_vector_search",
                    "operation": "parse_result",
                    "vertical": vertical,
                    "product_type": config.singular,
                    "validation_errors": e.errors(),
                    "raw_data": result_dict,  # Include for debugging
                    "expected_schema": config.dto_class.model_json_schema(),
                }
            ) from e
        
        # Build metadata dict using registry config
        metadata = {}
        for field_name in config.metadata_fields:
            value = getattr(dto, field_name, None)
            if value is not None:  # Only include non-None values
                metadata[field_name] = value
        
        # Map DTO fields to ProductResult using registry
        return ProductResult(
            product_id=getattr(dto, config.id_field),
            product_type=config.singular,
            title=getattr(dto, config.title_field),
            description=getattr(dto, config.description_field, None),
            relevance_score=getattr(dto, "score", 0.0),
            metadata=metadata,
        )
