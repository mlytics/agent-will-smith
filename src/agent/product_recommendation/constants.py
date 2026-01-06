"""Constants and enums for product recommendation agent.

Centralized constants to avoid duplication across codebase.
When adding a new vertical, update VERTICALS here and it propagates everywhere.
"""

from typing import Literal

# Supported product verticals
VERTICALS = Literal["activities", "books", "articles"]

# List of all verticals (for defaults and validation)
ALL_VERTICALS = ["activities", "books", "articles"]

# Default verticals to search if none specified
DEFAULT_VERTICALS = ALL_VERTICALS

# Timeout configurations
VECTOR_SEARCH_TIMEOUT_SECONDS = 5.0
INTENT_ANALYSIS_TIMEOUT_SECONDS = 10.0

