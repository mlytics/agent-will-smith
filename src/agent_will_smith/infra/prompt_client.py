"""Prompt client for MLflow prompt registry loading.

Centralized prompt management from MLflow registry.
Generic client that can be used by any agent.
Supports fallback to local files when MLflow GenAI is not available.
"""

import os
from pathlib import Path

import structlog

from agent_will_smith.core.exceptions import UpstreamError, UpstreamTimeoutError


class PromptClient:
    """Client for loading prompts from MLflow registry or local files.

    Provides centralized prompt management.
    Generic - can be used by any agent that needs prompts.
    Supports fallback to local files when MLflow GenAI module is unavailable.
    """

    def __init__(self, prompt_cache_ttl: int, fallback_prompts_dir: str | None = None):
        """Initialize prompt client.

        Args:
            prompt_cache_ttl: Cache TTL in seconds (None = use MLflow default, 0 = no cache)
            fallback_prompts_dir: Directory for fallback prompt files when MLflow unavailable
        """
        self.prompt_cache_ttl = prompt_cache_ttl
        self.fallback_prompts_dir = fallback_prompts_dir
        self.logger = structlog.get_logger(__name__)
        self._prompt_cache: dict[str, str] = {}

        # Check if mlflow.genai is available
        self._mlflow_genai_available = self._check_mlflow_genai()

    def _check_mlflow_genai(self) -> bool:
        """Check if mlflow.genai.load_prompt is available and working."""
        try:
            import mlflow.genai
            # Check if load_prompt function exists
            if not hasattr(mlflow.genai, "load_prompt"):
                self.logger.warning(
                    "mlflow.genai.load_prompt not available, will use fallback prompts",
                )
                return False
            return True
        except (ImportError, AttributeError):
            self.logger.warning(
                "mlflow.genai not available, will use fallback prompts",
            )
            return False

    def load_prompt(self, prompt_path: str) -> str:
        """Load prompt from MLflow registry or fallback file.

        Args:
            prompt_path: Prompt registry path (format: "prompts:/name/version")
                        Must start with "prompts:/" (single slash)

        Returns:
            Prompt text as string

        Raises:
            UpstreamTimeoutError: MLflow timeout
            UpstreamError: Other MLflow/file errors
        """
        # Check cache first
        if prompt_path in self._prompt_cache:
            self.logger.debug("returning cached prompt", prompt_path=prompt_path)
            return self._prompt_cache[prompt_path]

        prompt_text = None

        # Try MLflow first if available
        if self._mlflow_genai_available:
            try:
                prompt_text = self._load_from_mlflow(prompt_path)
            except Exception as e:
                self.logger.warning(
                    "mlflow prompt load failed, trying fallback",
                    prompt_path=prompt_path,
                    error=str(e),
                )

        # Fallback to local file
        if prompt_text is None:
            prompt_text = self._load_from_fallback(prompt_path)

        # Cache the prompt
        self._prompt_cache[prompt_path] = prompt_text
        return prompt_text

    def _load_from_mlflow(self, prompt_path: str) -> str:
        """Load prompt from MLflow GenAI registry."""
        import mlflow.genai

        self.logger.info(
            "loading prompt from mlflow",
            prompt_path=prompt_path,
            cache_ttl_seconds=self.prompt_cache_ttl
        )

        try:
            prompt = mlflow.genai.load_prompt(prompt_path, cache_ttl_seconds=self.prompt_cache_ttl)
            prompt_text = prompt.format()

            self.logger.info(
                "prompt loaded successfully from mlflow",
                prompt_path=prompt_path,
                prompt_length=len(prompt_text)
            )
            return prompt_text

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

    def _load_from_fallback(self, prompt_path: str) -> str:
        """Load prompt from fallback file.

        Converts prompt path like "prompts:/test.intent_chat_system/1"
        to file path like "{fallback_dir}/test.intent_chat_system.txt"
        """
        if not self.fallback_prompts_dir:
            raise UpstreamError(
                "MLflow GenAI unavailable and no fallback directory configured",
                details={
                    "prompt_path": prompt_path,
                    "suggestion": "Set CORE_PROMPT_FALLBACK_DIR or upgrade MLflow",
                }
            )

        # Parse prompt path: "prompts:/name/version" -> "name"
        prompt_name = prompt_path.replace("prompts:/", "").split("/")[0]
        fallback_file = Path(self.fallback_prompts_dir) / f"{prompt_name}.txt"

        self.logger.info(
            "loading prompt from fallback file",
            prompt_path=prompt_path,
            fallback_file=str(fallback_file)
        )

        try:
            prompt_text = fallback_file.read_text(encoding="utf-8")
            self.logger.info(
                "prompt loaded successfully from fallback",
                prompt_path=prompt_path,
                prompt_length=len(prompt_text)
            )
            return prompt_text

        except FileNotFoundError as e:
            raise UpstreamError(
                "Fallback prompt file not found",
                details={
                    "prompt_path": prompt_path,
                    "fallback_file": str(fallback_file),
                    "suggestion": f"Create file: {fallback_file}",
                }
            ) from e
        except Exception as e:
            raise UpstreamError(
                "Failed to load fallback prompt",
                details={
                    "prompt_path": prompt_path,
                    "fallback_file": str(fallback_file),
                    "error": str(e),
                }
            ) from e
