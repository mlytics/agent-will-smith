"""Prompt client for MLflow prompt registry loading.

Centralized prompt management from MLflow registry.
Generic client that can be used by any agent.
"""

import mlflow
import structlog

from agent_will_smith.core.exceptions import UpstreamError, UpstreamTimeoutError


class PromptClient:
    """Client for loading prompts from MLflow registry.

    Provides centralized prompt management.
    Generic - can be used by any agent that needs MLflow prompts.
    """

    def __init__(self, prompt_cache_ttl: int):
        """Initialize prompt client.

        Args:
            prompt_cache_ttl: Cache TTL in seconds (None = use MLflow default, 0 = no cache)
        """
        self.prompt_cache_ttl = prompt_cache_ttl
        self.logger = structlog.get_logger(__name__)

    def load_prompt(self, prompt_path: str) -> str:
        """Load prompt from MLflow registry.

        Args:
            prompt_path: Prompt registry path (format: "prompts:/catalog.schema.name/version")
                        Must start with "prompts:/" (single slash)

        Returns:
            Prompt text as string

        Raises:
            UpstreamTimeoutError: MLflow timeout
            UpstreamError: Other MLflow errors
        """

        self.logger.info(
            "loading prompt from mlflow",
            prompt_path=prompt_path,
            cache_ttl_seconds=self.prompt_cache_ttl
        )

        try:
            prompt = mlflow.genai.load_prompt(prompt_path, cache_ttl_seconds=self.prompt_cache_ttl)

            # Extract text from MLflow prompt object
            prompt_text = prompt.format()

            self.logger.info(
                "prompt loaded successfully",
                prompt_path=prompt_path,
                prompt_length=len(prompt_text)
            )
        except TimeoutError as e:
            raise UpstreamTimeoutError(
                "MLflow prompt load timed out",
                details={
                    "provider": "mlflow",
                    "operation": "load_prompt",
                    "prompt_path": prompt_path,
                }
            ) from e
        except Exception as e:
            raise UpstreamError(
                "Failed to load prompt from MLflow",
                details={
                    "provider": "mlflow",
                    "operation": "load_prompt",
                    "prompt_path": prompt_path,
                    "error": str(e),
                }
            ) from e

        return prompt_text
