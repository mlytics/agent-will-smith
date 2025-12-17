"""Core tools library for vector search and data retrieval.

Contains reusable, deterministic tools following the guidelines:
- Tools are small and single-purpose
- Tools return structured data, not English
- Tools are deterministic at the interface level

Note: 
- Direct functions (search_activities_direct, search_books_direct) for simple use
- @tool decorated versions (search_activities, search_books) for future LangGraph
"""

from core.tools.vector_search import (
    search_activities_direct,
    search_books_direct,
    search_activities,  # For future LangGraph use
    search_books,       # For future LangGraph use
)

__all__ = [
    "search_activities_direct",
    "search_books_direct",
    "search_activities",
    "search_books",
]

