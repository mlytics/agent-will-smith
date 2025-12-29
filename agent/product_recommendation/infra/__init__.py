"""Infrastructure layer - data access and external services.

Provides:
- vector_search: Databricks vector search functionality (3 verticals)
- prompts: MLflow prompt loading
"""

from agent.product_recommendation.infra.vector_search import (
    search_activities_direct,
    search_books_direct,
    search_articles_direct,
)
from agent.product_recommendation.infra.prompts import load_prompt_from_registry

__all__ = [
    "search_activities_direct",
    "search_books_direct",
    "search_articles_direct",
    "load_prompt_from_registry",
]

