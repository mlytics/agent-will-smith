"""MLFlow prompt loading utilities.

Centralized prompt management from MLFlow registry.
Follows guideline: "Make configuration declarative."
"""

import mlflow
import structlog
from typing import Any

from app.config import settings

logger = structlog.get_logger(__name__)


def load_prompt_from_registry(prompt_name: str | None = None) -> Any:
    """Load prompt from MLFlow registry.

    Args:
        prompt_name: Prompt registry path (e.g., "prompts:/catalog.schema.name/version")
                    If None, uses settings.prompt_name

    Returns:
        Loaded prompt object from MLFlow

    Raises:
        Exception: If prompt cannot be loaded
    """
    prompt_path = prompt_name or settings.prompt_name

    try:
        logger.info("loading_prompt", prompt_path=prompt_path)
        prompt = mlflow.genai.load_prompt(prompt_path)
        logger.info("prompt_loaded", prompt_path=prompt_path)
        return prompt

    except Exception as e:
        logger.error(
            "prompt_load_failed",
            prompt_path=prompt_path,
            error=str(e),
            exc_info=True,
        )
        raise


def format_prompt_with_variables(prompt: Any, **variables) -> str:
    """Format a loaded prompt with variables.

    Args:
        prompt: Loaded MLFlow prompt
        **variables: Variables to interpolate into prompt

    Returns:
        Formatted prompt string
    """
    try:
        return prompt.format(**variables)
    except KeyError as e:
        logger.error(
            "prompt_format_failed",
            missing_variable=str(e),
            provided_variables=list(variables.keys()),
            exc_info=True,
        )
        raise

