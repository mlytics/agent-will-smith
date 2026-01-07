"""MLflow prompt loading utilities with caching.

Centralized prompt management from MLflow registry.
Follows guideline: "Make configuration declarative."

CRITICAL REQUIREMENT: All prompts must be loaded from Databricks MLflow,
not hardcoded. This ensures proper versioning, governance, and tracking.

Caching: Prompts are cached in memory after first load for performance.
"""

import mlflow
import structlog
from functools import lru_cache

from src.agent.product_recommendation.config import ProductRecommendationAgentConfig
from src.agent.product_recommendation.schemas import PromptContent
from src.core.exceptions import BadRequestError, UpstreamError, UpstreamTimeoutError


@lru_cache(maxsize=10)
def load_prompt_from_registry(
    prompt_name: str | None = None,
    config: ProductRecommendationAgentConfig | None = None,
    logger: structlog.BoundLogger | None = None,
) -> PromptContent:
    """Load prompt from MLflow prompt registry with caching.

    Caching: Uses @lru_cache to cache prompts in memory after first load.
    Subsequent calls return cached version (no MLflow API call).

    Args:
        prompt_name: Prompt registry path (format: "prompts:/catalog.schema.name/version")
                    Must start with "prompts:/" (single slash)
                    If None, uses config.prompt_name
        config: Agent configuration instance (injected).
               If None, will load default ProductRecommendationAgentConfig()
        logger: Logger instance (injected).
               If None, will create default logger

    Returns:
        PromptContent (Pydantic model with validated text)
        Cached after first load for performance.

    Raises:
        Exception: If prompt cannot be loaded (by design - no silent failures)
    """
    # Load config if not provided (for backward compatibility)
    if config is None:
        config = ProductRecommendationAgentConfig()

    # Load logger if not provided
    if logger is None:
        logger = structlog.get_logger(__name__)

    prompt_path = prompt_name or config.prompt_name

    # Validate prompt path format
    if not prompt_path.startswith("prompts:/"):
        raise BadRequestError(
            f"Invalid prompt path format: {prompt_path}",
            details={
                "prompt_path": prompt_path,
                "expected_format": "prompts:/catalog.schema.name/version",
            }
        )

    logger.info("loading_prompt_from_mlflow", prompt_path=prompt_path)

    try:
        # Use MLflow's dedicated prompt loading API
        # Format: prompts:/catalog.schema.prompt_name/version (single slash!)
        prompt = mlflow.genai.load_prompt(prompt_path)

        # This is the standard way to extract text from MLflow prompt objects
        prompt_text = prompt.format()

        logger.info(
            "prompt_loaded_successfully", prompt_path=prompt_path, prompt_length=len(prompt_text)
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

    # Validate with Pydantic
    prompt_content = PromptContent(text=prompt_text, source=prompt_path)

    return prompt_content
