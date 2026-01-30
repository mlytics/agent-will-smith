"""Generic vector search client for Databricks Vector Search.

Injectable client class for vector similarity search with dependency injection support.
Provides low-level access to Databricks Vector Search without product-specific assumptions.
"""

from typing import TYPE_CHECKING

from databricks.vector_search.client import VectorSearchClient as DatabricksVectorSearchClient
import structlog
import mlflow

from agent_will_smith.core.exceptions import UpstreamError

if TYPE_CHECKING:
    from agent_will_smith.infra.embedding_client import EmbeddingClient


class VectorSearchClient:
    """Generic client for Databricks Vector Search with dependency injection support.

    This client provides storage-agnostic vector similarity search.
    Product-specific logic (column selection, result parsing) lives in agent repository layer.

    The DI container manages the lifecycle as a singleton.
    """

    def __init__(
        self,
        workspace_url: str,
        client_id: str,
        client_secret: str,
        endpoint_name: str,
        embedding_client: "EmbeddingClient",
    ):
        """Initialize vector search client with configuration.

        Args:
            workspace_url: Databricks workspace URL
            client_id: Service principal client ID
            client_secret: Service principal client secret
            endpoint_name: Vector search endpoint name
            embedding_client: Client for generating text embeddings
        """
        self.endpoint_name = endpoint_name
        self._embedding_client = embedding_client
        self.logger = structlog.get_logger(__name__)
        self._client = DatabricksVectorSearchClient(
            workspace_url=workspace_url,
            service_principal_client_id=client_id,
            service_principal_client_secret=client_secret,
            disable_notice=True,
        )
        self.logger.info("vector search client initialized", endpoint=endpoint_name)

    @mlflow.trace(name="databricks_vector_search_api")
    def similarity_search(
        self,
        index_name: str,
        query_text: str,
        columns: list[str],
        num_results: int,
        filters: dict | str | None = None,
    ) -> dict:
        """Execute similarity search and return raw results.

        This is a generic method that performs low-level vector search.
        Query text is embedded using Gemini before searching.
        All product-specific logic (column selection, result parsing) is handled
        by the caller (typically a repository layer).

        Args:
            index_name: Name of the vector search index
            query_text: Query text for similarity search
            columns: List of column names to retrieve
            num_results: Maximum number of results
            filters: Optional filters - dict for equality or string for SQL-like expressions

        Returns:
            Raw dict response from Databricks Vector Search API
            Format: {"result": {"data_array": [...], "manifest": {...}}}

        Raises:
            UpstreamError: If embedding or vector search fails
        """
        self.logger.info(
            "vector search starting",
            index_name=index_name,
            query_length=len(query_text),
            num_results=num_results,
            columns=columns,
            filters=filters,
        )

        try:
            # Embed query text using embedding client
            query_vector = self._embedding_client.embed_text(query_text)

            # Get vector search index
            index = self._client.get_index(
                endpoint_name=self.endpoint_name,
                index_name=index_name
            )

            results = index.similarity_search(
                query_text=query_text,
                query_vector=query_vector,
                columns=columns,
                filters=filters,
                num_results=num_results,
                query_type="HYBRID",
            )

            self.logger.info("vector search completed", index_name=index_name)
            return results

        except UpstreamError:
            raise
        except Exception as e:
            self.logger.error(
                "vector search failed",
                index_name=index_name,
                error_type=type(e).__name__,
                error=str(e),
                exc_info=e,
            )
            raise UpstreamError(
                f"Vector search failed: {type(e).__name__}: {str(e)}",
                details={
                    "provider": "databricks_vector_search",
                    "operation": "similarity_search",
                    "index_name": index_name,
                    "error_type": type(e).__name__,
                    "error": str(e),
                }
            ) from e
