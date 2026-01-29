"""Embedding client for text vectorization.

Generic injectable client for generating text embeddings with dependency injection support.
Shared across all agents that need embedding capabilities.
"""

import math

from google import genai
from google.genai import types
import structlog
import mlflow

from agent_will_smith.core.exceptions import UpstreamError


class EmbeddingClient:
    """Generic client for text embeddings with dependency injection support.

    This client provides text embedding generation using Google's Gemini API.
    The DI container manages the lifecycle as a singleton.
    Fully generic - can be used by any agent.
    """

    def __init__(
        self,
        api_key: str,
        model_name: str,
        dimension: int,
    ):
        """Initialize embedding client with configuration.

        Args:
            api_key: Google API key for Gemini
            model_name: Gemini embedding model name
            dimension: Output embedding dimension
        """
        self._model_name = model_name
        self._dimension = dimension
        self.logger = structlog.get_logger(__name__)
        self._client = genai.Client(api_key=api_key)
        self.logger.info(
            "embedding client initialized",
            model=model_name,
            dimension=dimension,
        )

    def _l2_normalize(self, vector: list[float]) -> list[float]:
        """L2 normalize a vector.

        Required when using reduced dimensionality embeddings per Gemini docs.

        Args:
            vector: Input vector to normalize.

        Returns:
            L2 normalized vector.
        """
        magnitude = math.sqrt(sum(x * x for x in vector))
        if magnitude == 0:
            return vector
        return [x / magnitude for x in vector]

    @mlflow.trace(name="gemini_embed_content")
    def embed_text(self, text: str, normalize: bool = True) -> list[float]:
        """Generate embedding for input text.

        Args:
            text: Input text to embed.
            normalize: Whether to L2 normalize the embedding (default: True).

        Returns:
            Embedding vector as list of floats.

        Raises:
            UpstreamError: If embedding generation fails.
        """
        try:
            response = self._client.models.embed_content(
                model=self._model_name,
                contents=text,
                config=types.EmbedContentConfig(
                    task_type="SEMANTIC_SIMILARITY",
                    output_dimensionality=self._dimension,
                ),
            )
            embedding = response.embeddings[0].values

            if normalize:
                embedding = self._l2_normalize(embedding)

            return embedding

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
                    "model": self._model_name,
                    "dimension": self._dimension,
                    "error_type": type(e).__name__,
                    "error": str(e),
                }
            ) from e
