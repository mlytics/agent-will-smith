"""Product configuration registry.

Injectable registry for product type configuration.
All configuration is built at runtime inside the class, not at import time.
"""

from typing import TYPE_CHECKING

from agent_will_smith.agent.product_recommendation.repo.dto import ActivityDTO, BookDTO, ArticleDTO
from agent_will_smith.agent.product_recommendation.model.types import Vertical

if TYPE_CHECKING:
    from agent_will_smith.agent.product_recommendation.config import Config


class ProductRegistry:
    """Injectable product configuration registry.
    
    All product configuration is constructed at instantiation time,
    not at module import time. This enables:
    - Testability (can mock/replace per test)
    - No global mutable state
    - Explicit initialization
    
    Injected via DI container.
    """

    def __init__(self, config: "Config"):
        """Initialize registry with all product configuration.
        
        Args:
            config: Agent configuration with individual index settings.
        """
        self._config = config
        
        # Product configuration - map verticals to DTOs
        # DTOs own their own transformation to ProductResult (explicit, type-safe)
        self._products: dict[Vertical, type[ActivityDTO | BookDTO | ArticleDTO]] = {
            Vertical.ACTIVITIES: ActivityDTO,
            Vertical.BOOKS: BookDTO,
            Vertical.ARTICLES: ArticleDTO,
        }
        
        # Map verticals to index names from individual config fields
        self._index_map: dict[Vertical, str] = {
            Vertical.ACTIVITIES: config.activities_index,
            Vertical.BOOKS: config.books_index,
            Vertical.ARTICLES: config.articles_index,
        }

    def _validate_completeness(self) -> None:
        """Validate all product types have configured indices."""
        missing = []
        for vertical in self._products:
            if vertical not in self._index_map or not self._index_map[vertical]:
                missing.append(vertical.value)
        
        if missing:
            raise ValueError(
                f"Missing product index configuration for: {', '.join(missing)}. "
                f"Set AGENT_PRODUCT_RECOMMENDATION_<VERTICAL>_INDEX environment variables."
            )

    def get_dto_class(self, vertical: Vertical) -> type[ActivityDTO | BookDTO | ArticleDTO]:
        """Get DTO class for a vertical."""
        return self._products[vertical]

    def get_index_name(self, vertical: Vertical) -> str:
        """Get vector search index name for a vertical."""
        return self._index_map[vertical]

    def get_columns(self, vertical: Vertical) -> list[str]:
        """Get columns to fetch for a vertical.

        Derived from DTO: all model fields except 'score'.
        Score is returned automatically by Databricks Vector Search,
        not stored as a column in the index.
        """
        dto_class = self._products[vertical]
        # Exclude 'score' - it's returned by vector search API, not a column
        return [col for col in dto_class.model_fields.keys() if col != "score"]
