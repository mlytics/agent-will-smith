"""Infrastructure layer - data access and external services.

Provides:
- vector_search: Databricks vector search functionality
- prompts: MLflow prompt loading
"""

from agent.product_recommendation.infra.vector_search import (
    search_activities,
    search_books,
    search_activities_direct,
    search_books_direct,
)
from agent.product_recommendation.infra.prompts import (
    load_prompt_from_registry,
    load_prompt_from_registry_with_fallback,
)

__all__ = [
    "search_activities",
    "search_books",
    "search_activities_direct",
    "search_books_direct",
    "load_prompt_from_registry",
    "load_prompt_from_registry_with_fallback",
]

