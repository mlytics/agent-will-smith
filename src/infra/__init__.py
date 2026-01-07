"""Shared infrastructure layer.

Provides generic, reusable clients that can be used by any agent:
- LLMClient: Generic LLM wrapper for Databricks
- VectorSearchClient: Generic vector similarity search
- PromptClient: MLflow prompt registry loader

Product-specific logic lives in agent repository layers.
"""

from src.infra.llm_client import LLMClient
from src.infra.vector_search_client import VectorSearchClient
from src.infra.prompt_client import PromptClient
from src.infra.container import Container as InfraContainer

__all__ = [
    "LLMClient",
    "VectorSearchClient",
    "PromptClient",
    "InfraContainer",
]
