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
        
        # Product configuration - just map verticals to DTOs
        # All field mappings derived from DTO methods (DRY principle)
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

    def get_config(self, vertical: Vertical) -> dict:
        """Get product configuration for a vertical (for backward compatibility).
        
        Returns dict with dto class and field names derived from DTO methods.
        """
        dto_class = self._products[vertical]
        return {
            "dto": dto_class,
            "id_field": dto_class.get_id_field(),
            "title_field": dto_class.get_title_field(),
            "description_field": dto_class.get_description_field(),
            "metadata_fields": dto_class.get_metadata_fields(),
        }

    def get_index_name(self, vertical: Vertical) -> str:
        """Get vector search index name for a vertical."""
        return self._index_map[vertical]

    def get_columns(self, vertical: Vertical) -> list[str]:
        """Get columns to fetch for a vertical.
        
        Derived from DTO: all model fields (metadata + id + title + description + score).
        """
        dto_class = self._products[vertical]
        return list(dto_class.model_fields.keys())
