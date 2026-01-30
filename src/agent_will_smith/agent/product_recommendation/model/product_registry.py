"""Product configuration registry.

Injectable registry for product type configuration.
All configuration is built at runtime inside the class, not at import time.
"""

from datetime import datetime, timezone
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

        Delegates to DTO which knows which fields are DB columns vs computed fields.
        """
        dto_class = self._products[vertical]
        return dto_class.get_db_columns()

    def get_availability_filter(self, vertical: Vertical) -> dict | None:
        """Return availability filter for a vertical (query-time).

        Business logic for per-vertical availability constraints.
        Databricks standard endpoints support comparison operators in dict keys:
        {"column >": value}, {"column <": value}, etc.

        Business rules:
        - Articles/Books: is_active = true
        - Activities: end_time > now

        Args:
            vertical: Product vertical to get filter for.

        Returns:
            Filter dict or None if no filter needed.
        """
        if vertical in (Vertical.ARTICLES, Vertical.BOOKS):
            return {"is_active": True}

        if vertical == Vertical.ACTIVITIES:
            now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
            return {"end_time >": now}

        return None
