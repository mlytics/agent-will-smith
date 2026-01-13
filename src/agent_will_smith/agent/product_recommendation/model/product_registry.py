"""Product configuration registry.

Injectable registry for product type configuration.
All configuration is built at runtime inside the class, not at import time.
"""

from typing import TYPE_CHECKING

from agent_will_smith.agent.product_recommendation.repo.dto import ActivityDTO, BookDTO, ArticleDTO
from agent_will_smith.agent.product_recommendation.model.types import VERTICALS

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
            config: Agent configuration with product_indices mapping.
        """
        self._config = config
        
        # Product configuration (built at init, not import)
        # All product-related config in one place - no separate mappings
        self._products: dict[VERTICALS, dict] = {
            "activities": {
                "dto": ActivityDTO,
                "id_field": "content_id",
                "title_field": "title",
                "description_field": "description",
                "columns": [
                    "content_id", "title", "description", "category",
                    "location_name", "location_address", "organizer",
                    "start_time", "end_time", "permalink_url", "cover_image_urls",
                ],
                "metadata_fields": [
                    "category", "location_name", "location_address", "organizer",
                    "start_time", "end_time", "permalink_url", "cover_image_urls",
                ],
            },
            "books": {
                "dto": BookDTO,
                "id_field": "content_id",
                "title_field": "title_main",
                "description_field": "description",
                "columns": [
                    "content_id", "title_main", "title_subtitle", "description",
                    "authors", "categories", "permalink_url", "cover_image_url", "prices",
                ],
                "metadata_fields": [
                    "title_subtitle", "authors", "categories",
                    "permalink_url", "cover_image_url", "prices",
                ],
            },
            "articles": {
                "dto": ArticleDTO,
                "id_field": "content_id",
                "title_field": "title",
                "description_field": "content",
                "columns": [
                    "content_id", "title", "content", "authors", "keywords",
                    "categories", "permalink_url", "thumbnail_url", "main_image_url", "publish_time",
                ],
                "metadata_fields": [
                    "authors", "keywords", "categories",
                    "permalink_url", "thumbnail_url", "main_image_url", "publish_time",
                ],
            },
        }
        
        self._validate_completeness()

    def _validate_completeness(self) -> None:
        """Validate all product types have configured indices."""
        missing = []
        for vertical in self._products:
            if vertical not in self._config.product_indices:
                missing.append(vertical)
        
        if missing:
            raise ValueError(
                f"Missing product index configuration for: {', '.join(missing)}. "
                f"Set AGENT_PRODUCT_RECOMMENDATION_PRODUCT_INDICES environment variable."
            )

    def get_config(self, vertical: VERTICALS) -> dict:
        """Get product configuration for a vertical."""
        return self._products[vertical]

    def get_index_name(self, vertical: VERTICALS) -> str:
        """Get vector search index name for a vertical."""
        return self._config.product_indices[vertical]

    def get_columns(self, vertical: VERTICALS) -> list[str]:
        """Get columns to fetch for a vertical."""
        return self._products[vertical]["columns"]
