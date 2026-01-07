"""Type definitions for product recommendation agent."""

from typing import Literal

# Supported product verticals (Literal type for static type checking)
VERTICALS = Literal["activities", "books", "articles"]
