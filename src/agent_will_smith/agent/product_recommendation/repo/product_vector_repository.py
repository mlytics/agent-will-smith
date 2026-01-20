"""Product vector search repository.

Repository for product-specific vector search operations.
Wraps generic VectorSearchClient and adds product-specific business logic:
- Column selection per product type
- Result parsing and transformation
- ProductResult construction

Uses injected ProductRegistry for configuration.
"""

from pydantic import ValidationError
import structlog

from agent_will_smith.infra.vector_search_client import VectorSearchClient
from agent_will_smith.agent.product_recommendation.model.product import ProductResult
from agent_will_smith.agent.product_recommendation.model.types import Vertical
from agent_will_smith.agent.product_recommendation.model.product_registry import ProductRegistry
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
        registry: ProductRegistry,
    ):
        """Initialize with injected dependencies.

        Args:
            vector_client: Generic vector search client
            registry: Product configuration registry
        """
        self.vector_client = vector_client
        self.registry = registry
        self.logger = structlog.get_logger(__name__)

    def search(
        self,
        vertical: Vertical,
        query: str,
        max_results: int,
        customer_uuid: str | None = None,
    ) -> list[ProductResult]:
        """Search a product vertical with product-specific logic.
        
        Generic method that works for all product types using the registry.
        
        Args:
            vertical: Product vertical to search ("activities", "books", "articles")
            query: Search query text
            max_results: Maximum number of results
            customer_uuid: Optional customer UUID for filtering
            
        Returns:
            List of ProductResult objects
        """
        index_name = self.registry.get_index_name(vertical)
        columns = self.registry.get_columns(vertical)

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

    def _parse_results(
        self,
        results: dict,
        vertical: Vertical,
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
        self, result_dict: dict, vertical: Vertical
    ) -> ProductResult:
        """Parse a single result row into ProductResult.
        
        DTO owns its own transformation - explicit field mapping, type-safe.
        
        Args:
            result_dict: Raw result dict from vector search
            vertical: Product vertical name
            
        Returns:
            ProductResult object
            
        Raises:
            UpstreamError: If data validation fails
        """
        dto_class = self.registry.get_dto_class(vertical)
        
        # Validate using product-specific DTO
        try:
            dto = dto_class.model_validate(result_dict)
        except ValidationError as e:
            raise UpstreamError(
                "Invalid data format from vector search",
                details={
                    "provider": "databricks_vector_search",
                    "operation": "parse_result",
                    "vertical": vertical,
                    "validation_errors": e.errors(),
                    "raw_data": result_dict,
                    "expected_schema": dto_class.model_json_schema(),
                }
            ) from e
        
        # DTO transforms itself - explicit, type-safe
        return dto.to_product_result(vertical)
