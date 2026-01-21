"""Type definitions for product recommendation agent."""

from enum import Enum


class Vertical(str, Enum):
    """Product verticals - enforced enum to prevent string sprawl.
    
    Using str, Enum for:
    - Pydantic/FastAPI JSON serialization (auto-converts to string)
    - Dict key compatibility
    - DRY: unified management, no repeated string checks
    """
    ACTIVITIES = "activities"
    BOOKS = "books"
    ARTICLES = "articles"
