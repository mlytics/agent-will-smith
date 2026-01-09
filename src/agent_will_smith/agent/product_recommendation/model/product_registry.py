"""Product type registry with centralized configuration.

Centralizes all product-specific configuration that was previously
scattered across repository methods, config fields, and node mappings.

This registry serves as the single source of truth for:
- Product type metadata (singular/plural forms)
- DTO class mappings
- Vector search column definitions
- Field mappings for ProductResult transformation
- Metadata field selections

Adding a new product type requires only updating this registry.
"""

from typing import Type, TYPE_CHECKING
from pydantic import BaseModel, Field
from agent_will_smith.agent.product_recommendation.repo.dto import ActivityDTO, BookDTO, ArticleDTO
from agent_will_smith.agent.product_recommendation.model.types import VERTICALS

if TYPE_CHECKING:
    from agent_will_smith.agent.product_recommendation.config import Config


class ProductTypeConfig(BaseModel):
    """Configuration for a single product type.
    
    Centralizes all product-specific configuration that was previously
    scattered across repository methods, config fields, and node mappings.
    """
    
    # Identity
    singular: str = Field(
        ...,
        description="Singular form used internally (e.g., 'activity')",
        examples=["activity"],
    )
    plural: str = Field(
        ...,
        description="Plural form used in API (e.g., 'activities')",
        examples=["activities"],
    )
    
    # Infrastructure
    dto_class: Type[BaseModel] = Field(
        ...,
        description="Pydantic DTO class for parsing vector search results",
    )
    index_config_key: str = Field(
        ...,
        description="Config field name for vector search index",
        examples=["activities_index"],
    )
    
    # Schema - Vector Search Columns
    columns: list[str] = Field(
        ...,
        description="Columns to fetch from vector search index",
        examples=[["content_id", "title", "description"]],
    )
    
    # Transformation - ProductResult Field Mapping
    id_field: str = Field(
        default="content_id",
        description="DTO field mapping to ProductResult.product_id",
        examples=["content_id"],
    )
    title_field: str = Field(
        default="title",
        description="DTO field mapping to ProductResult.title",
        examples=["title", "title_main"],
    )
    description_field: str = Field(
        default="description",
        description="DTO field mapping to ProductResult.description",
        examples=["description", "content"],
    )
    
    # Metadata - Fields to Include in ProductResult.metadata
    metadata_fields: list[str] = Field(
        ...,
        description="DTO fields to include in ProductResult.metadata dict",
        examples=[["category", "location_name", "organizer"]],
    )

    class Config:
        arbitrary_types_allowed = True  # Allow Type[BaseModel]


# Registry - Single Source of Truth for All Product Types
PRODUCT_TYPES: dict[VERTICALS, ProductTypeConfig] = {
    "activities": ProductTypeConfig(
        singular="activity",
        plural="activities",
        dto_class=ActivityDTO,
        index_config_key="activities_index",
        columns=[
            "content_id",
            "title",
            "description",
            "category",
            "location_name",
            "location_address",
            "organizer",
            "start_time",
            "end_time",
            "permalink_url",
            "cover_image_urls",
        ],
        id_field="content_id",
        title_field="title",
        description_field="description",
        metadata_fields=[
            "category",
            "location_name",
            "location_address",
            "organizer",
            "start_time",
            "end_time",
            "permalink_url",
            "cover_image_urls",
        ],
    ),
    "books": ProductTypeConfig(
        singular="book",
        plural="books",
        dto_class=BookDTO,
        index_config_key="books_index",
        columns=[
            "content_id",
            "title_main",
            "title_subtitle",
            "description",
            "authors",
            "categories",
            "permalink_url",
            "cover_image_url",
            "prices",
        ],
        id_field="content_id",
        title_field="title_main",
        description_field="description",
        metadata_fields=[
            "title_subtitle",
            "authors",
            "categories",
            "permalink_url",
            "cover_image_url",
            "prices",
        ],
    ),
    "articles": ProductTypeConfig(
        singular="article",
        plural="articles",
        dto_class=ArticleDTO,
        index_config_key="articles_index",
        columns=[
            "content_id",
            "title",
            "content",
            "authors",
            "keywords",
            "categories",
            "permalink_url",
            "thumbnail_url",
            "main_image_url",
            "publish_time",
        ],
        id_field="content_id",
        title_field="title",
        description_field="content",
        metadata_fields=[
            "authors",
            "keywords",
            "categories",
            "permalink_url",
            "thumbnail_url",
            "main_image_url",
            "publish_time",
        ],
    ),
}


# Utility Functions

def get_product_config(vertical: VERTICALS) -> ProductTypeConfig:
    """Get product configuration by vertical name.
    
    Args:
        vertical: Product vertical (plural form: "activities", "books", "articles")
        
    Returns:
        ProductTypeConfig for the vertical
        
    Raises:
        KeyError: If vertical is not registered
        
    Example:
        >>> config = get_product_config("activities")
        >>> config.singular
        "activity"
    """
    return PRODUCT_TYPES[vertical]


def validate_config_completeness(config: "Config") -> None:  # noqa: F821
    """Validate that all product types have required index configurations.
    
    Call this during application startup to fail fast if configuration is incomplete.
    
    Args:
        config: Agent configuration to validate
        
    Raises:
        ValueError: If any product type is missing its index configuration
        
    Example:
        >>> from agent_will_smith.agent.product_recommendation.config import Config
        >>> config = Config()
        >>> validate_config_completeness(config)  # Raises if incomplete
    """
    missing_configs = []
    
    for vertical, product_config in PRODUCT_TYPES.items():
        index_name = getattr(config, product_config.index_config_key, None)
        if not index_name:
            missing_configs.append(product_config.index_config_key)
    
    if missing_configs:
        raise ValueError(
            f"Missing required index configurations: {', '.join(missing_configs)}. "
            f"Check environment variables: {', '.join(f'AGENT_PRODUCT_RECOMMENDATION_{k.upper()}' for k in missing_configs)}"
        )


def plural_to_singular(vertical: VERTICALS) -> str:
    """Convert API plural form to internal singular form.
    
    Args:
        vertical: Plural form ("activities", "books", "articles")
        
    Returns:
        Singular form ("activity", "book", "article")
        
    Example:
        >>> plural_to_singular("activities")
        "activity"
    """
    return PRODUCT_TYPES[vertical].singular


def singular_to_plural(product_type: str) -> VERTICALS:
    """Convert internal singular form to API plural form.
    
    Args:
        product_type: Singular form ("activity", "book", "article")
        
    Returns:
        Plural form ("activities", "books", "articles")
        
    Raises:
        ValueError: If product_type is not a registered singular form
        
    Example:
        >>> singular_to_plural("activity")
        "activities"
    """
    for vertical, config in PRODUCT_TYPES.items():
        if config.singular == product_type:
            return vertical
    
    raise ValueError(
        f"Unknown product type: {product_type}. "
        f"Valid types: {', '.join(c.singular for c in PRODUCT_TYPES.values())}"
    )


def get_all_verticals() -> list[VERTICALS]:
    """Get list of all registered product verticals.
    
    Returns:
        List of vertical names (plural forms)
        
    Example:
        >>> get_all_verticals()
        ["activities", "books", "articles"]
    """
    return list(PRODUCT_TYPES.keys())

