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

logger = structlog.get_logger(__name__)


def load_prompt_from_registry(prompt_name: str | None = None) -> str:
    """Load prompt from MLflow registry (Unity Catalog).
    
    This is the ONLY way prompts should be loaded. No hardcoded fallbacks
    for production use.
    
    Args:
        prompt_name: Prompt registry path (format: "models:/catalog.schema.name/version")
                    If None, uses config.prompt_name
    
    Returns:
        Prompt text string
        
    Raises:
        Exception: If prompt cannot be loaded (by design - no silent failures)
    """
    prompt_path = prompt_name or config.prompt_name
    
    try:
        logger.info("loading_prompt_from_mlflow", prompt_path=prompt_path)
        
        # Parse the model URI
        # Format: models:/catalog.schema.model_name/version
        from mlflow.tracking import MlflowClient
        
        client = MlflowClient()
        
        # Extract model name and version from path
        model_path = prompt_path.replace("models:/", "")
        model_name, version = model_path.rsplit("/", 1)
        
        # Get model version details
        model_version = client.get_model_version(model_name, version)
        run_id = model_version.run_id
        
        logger.info("prompt_model_found",
                   model_name=model_name,
                   version=version,
                   run_id=run_id)
        
        # Download the prompt artifact from the run
        artifact_path = mlflow.artifacts.download_artifacts(
            run_id=run_id,
            artifact_path="system_prompt.txt"
        )
        
        # Read the prompt text
        with open(artifact_path, 'r') as f:
            prompt_text = f.read()
        
        logger.info("prompt_loaded_successfully",
                   prompt_path=prompt_path,
                   prompt_length=len(prompt_text),
                   version=version)
        
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
        if fallback_prompt and config.environment == "development":
            logger.warning(
                "using_fallback_prompt_dev_only",
                error=str(e),
                environment=config.environment
            )
            return fallback_prompt
        else:
            # In production, always fail hard
            logger.error(
                "prompt_load_failed_no_fallback",
                environment=config.environment
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

