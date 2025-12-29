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

