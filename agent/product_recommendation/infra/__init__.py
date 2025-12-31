"""Infrastructure layer - data access and external services.

Provides:
- vector_search: Databricks vector search functionality (3 verticals)
- llm_client: Pooled LLM client (ChatDatabricks)
- prompts: MLflow prompt loading with caching
"""

from agent.product_recommendation.infra.vector_search import (
    search_activities_direct,
    search_books_direct,
    search_articles_direct,
    get_vector_search_client,
)
from agent.product_recommendation.infra.llm_client import get_llm_client
from agent.product_recommendation.infra.prompts import load_prompt_from_registry

__all__ = [
    "search_activities_direct",
    "search_books_direct",
    "search_articles_direct",
    "get_vector_search_client",
    "get_llm_client",
    "load_prompt_from_registry",
]

