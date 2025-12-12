"""Core tools library for vector search and data retrieval.

Contains reusable, deterministic tools following the guidelines:
- Tools are small and single-purpose
- Tools return structured data, not English
- Tools are deterministic at the interface level
"""

from core.tools.vector_search import search_activities, search_books

__all__ = ["search_activities", "search_books"]

