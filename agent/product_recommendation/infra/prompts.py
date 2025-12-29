"""MLflow prompt loading utilities.

Centralized prompt management from MLflow registry.
Follows guideline: "Make configuration declarative."

CRITICAL REQUIREMENT: All prompts must be loaded from Databricks MLflow,
not hardcoded. This ensures proper versioning, governance, and tracking.
"""

import mlflow
import structlog
from typing import Any

from core.config import config
from agent.product_recommendation.config import agent_config

logger = structlog.get_logger(__name__)


def load_prompt_from_registry(prompt_name: str | None = None) -> str:
    """Load prompt from MLflow prompt registry (Unity Catalog).
    
    This is the ONLY way prompts should be loaded. No hardcoded fallbacks
    for production use.
    
    IMPORTANT: Prompt must be created in Databricks UI first using the
    "Create Prompt" feature in Unity Catalog.
    
    Args:
        prompt_name: Prompt registry path (format: "prompts:/catalog.schema.name/version")
                    Must start with "prompts:/" (single slash)
                    If None, uses config.prompt_name
    
    Returns:
        Prompt text string
        
    Raises:
        Exception: If prompt cannot be loaded (by design - no silent failures)
    """
    prompt_path = prompt_name or agent_config.prompt_name
    
    # Validate prompt path format
    if not prompt_path.startswith("prompts:/"):
        raise ValueError(
            f"Invalid prompt path format: {prompt_path}. "
            f"Must start with 'prompts:/' (e.g., prompts:/catalog.schema.name/version)"
        )
    
    try:
        logger.info("loading_prompt_from_mlflow", prompt_path=prompt_path)
        
        # Use MLflow's dedicated prompt loading API
        # Format: prompts:/catalog.schema.prompt_name/version (single slash!)
        prompt = mlflow.genai.load_prompt(prompt_path)
        
        # Use .format() method to get the prompt text
        # This is the standard way to extract text from MLflow prompt objects
        prompt_text = prompt.format()
        
        logger.info("prompt_loaded_successfully",
                   prompt_path=prompt_path,
                   prompt_length=len(prompt_text))
        
        return prompt_text
        
    except Exception as e:
        logger.error(
            "prompt_load_failed",
            prompt_path=prompt_path,
            error=str(e),
            error_type=type(e).__name__,
            exc_info=True,
        )
        raise  # Re-raise - no silent failures!


def load_prompt_from_registry_with_fallback(
    prompt_name: str | None = None,
    fallback_prompt: str | None = None
) -> str:
    """Load prompt with optional fallback (for development only).
    
    ⚠️ WARNING: Use only in development! Production should always load from registry.
    
    Args:
        prompt_name: Prompt registry path
        fallback_prompt: Fallback prompt text if loading fails (dev only)
        
    Returns:
        Prompt text (from registry or fallback)
    """
    try:
        return load_prompt_from_registry(prompt_name)
    except Exception as e:
        # Import here to avoid circular dependency
        from core.config import config
        if fallback_prompt and config.fastapi.environment == "development":
            logger.warning(
                "using_fallback_prompt_dev_only",
                error=str(e),
                environment=config.fastapi.environment
            )
            return fallback_prompt
        else:
            # In production, always fail hard
            logger.error(
                "prompt_load_failed_no_fallback",
                environment=config.fastapi.environment
            )
            raise


def format_prompt_with_variables(prompt: str, **variables) -> str:
    """Format a prompt with variables.
    
    Args:
        prompt: Prompt text with placeholders
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

