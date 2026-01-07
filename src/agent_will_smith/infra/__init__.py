"""Shared infrastructure layer.

Provides generic, reusable clients that can be used by any agent:
- LLMClient: Generic LLM wrapper for Databricks
- VectorSearchClient: Generic vector similarity search
- PromptClient: MLflow prompt registry loader

Product-specific logic lives in agent repository layers.
"""

from agent_will_smith.infra.llm_client import LLMClient
from agent_will_smith.infra.vector_search_client import VectorSearchClient
from agent_will_smith.infra.prompt_client import PromptClient
from agent_will_smith.infra.container import Container as InfraContainer

__all__ = [
    "LLMClient",
    "VectorSearchClient",
    "PromptClient",
    "InfraContainer",
]
