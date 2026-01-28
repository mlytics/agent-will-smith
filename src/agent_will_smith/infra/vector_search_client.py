"""Generic vector search client for Databricks Vector Search.

Injectable client class for vector similarity search with dependency injection support.
Provides low-level access to Databricks Vector Search without product-specific assumptions.
"""

import math

from databricks.vector_search.client import VectorSearchClient as DatabricksVectorSearchClient
from google import genai
from google.genai import types
import structlog
import mlflow

from agent_will_smith.core.exceptions import UpstreamError


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
        gemini_api_key: str,
        gemini_embedding_model: str,
        gemini_embedding_dimension: int,
    ):
        """Initialize vector search client with configuration.

        Args:
            workspace_url: Databricks workspace URL
            client_id: Service principal client ID
            client_secret: Service principal client secret
            endpoint_name: Vector search endpoint name
            gemini_api_key: Gemini API key for embeddings
            gemini_embedding_model: Gemini embedding model name
            gemini_embedding_dimension: Output dimension for embeddings
        """
        self.endpoint_name = endpoint_name
        self._gemini_embedding_model = gemini_embedding_model
        self._gemini_embedding_dimension = gemini_embedding_dimension
        self.logger = structlog.get_logger(__name__)
        self._client = DatabricksVectorSearchClient(
            workspace_url=workspace_url,
            service_principal_client_id=client_id,
            service_principal_client_secret=client_secret,
            disable_notice=True,
        )
        self._gemini_client = genai.Client(api_key=gemini_api_key)
        self.logger.info(
            "vector search client initialized",
            endpoint=endpoint_name,
            embedding_model=gemini_embedding_model,
            embedding_dimension=gemini_embedding_dimension,
        )

    def _normalize(self, vector: list[float]) -> list[float]:
        """L2 normalize a vector.

        Required when using reduced dimensionality embeddings per Gemini docs.
        """
        magnitude = math.sqrt(sum(x * x for x in vector))
        if magnitude == 0:
            return vector
        return [x / magnitude for x in vector]

    @mlflow.trace(name="gemini_embed_content")
    def _embed_query(self, query_text: str) -> list[float]:
        """Embed query text using Gemini.

        Args:
            query_text: Text to embed

        Returns:
            Normalized embedding vector as list of floats

        Raises:
            UpstreamError: If embedding fails
        """
        try:
            response = self._gemini_client.models.embed_content(
                model=self._gemini_embedding_model,
                contents=query_text,
                config=types.EmbedContentConfig(
                    task_type="SEMANTIC_SIMILARITY",
                    output_dimensionality=self._gemini_embedding_dimension,
                ),
            )
            return self._normalize(response.embeddings[0].values)
        except Exception as e:
            self.logger.error(
                "gemini embedding failed",
                error_type=type(e).__name__,
                error=str(e),
                exc_info=e,
            )
            raise UpstreamError(
                f"Gemini embedding failed: {type(e).__name__}: {str(e)}",
                details={
                    "provider": "gemini",
                    "operation": "embed_content",
                    "model": self._gemini_embedding_model,
                    "dimension": self._gemini_embedding_dimension,
                    "error_type": type(e).__name__,
                    "error": str(e),
                }
            ) from e

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
            # Embed query text using Gemini
            query_vector = self._embed_query(query_text)

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
