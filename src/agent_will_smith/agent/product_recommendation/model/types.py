"""Type definitions for product recommendation agent."""

from datetime import datetime, timezone
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

    def get_availability_filter(self) -> dict | None:
        """Return availability filter for this vertical (query-time).

        All filtering business logic lives here.
        Databricks standard endpoints support comparison operators in dict keys:
        {"column >": value}, {"column <": value}, etc.

        Business rules:
        - Articles/Books: is_active = true
        - Activities: end_time > now

        Returns:
            Filter dict or None if no filter needed
        """
        if self in (Vertical.ARTICLES, Vertical.BOOKS):
            return {"is_active": True}

        if self == Vertical.ACTIVITIES:
            now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
            return {"end_time >": now}

        return None
