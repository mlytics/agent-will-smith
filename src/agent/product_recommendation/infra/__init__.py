"""Infrastructure layer - data access and external services.

Provides injectable client classes following the joke_agent pattern:
- VectorSearchClient: Databricks vector search functionality
- LLMClient: LLM client for Databricks endpoints
- prompts: MLflow prompt loading with caching
"""

from src.agent.product_recommendation.infra.vector_search import VectorSearchClient
from src.agent.product_recommendation.infra.llm_client import LLMClient
from src.agent.product_recommendation.infra.prompts import load_prompt_from_registry

__all__ = [
    "VectorSearchClient",
    "LLMClient",
    "load_prompt_from_registry",
]
