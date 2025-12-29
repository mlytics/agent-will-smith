"""Deterministic query builder for vector search.

Constructs search queries from article, question, and intent WITHOUT using LLM.
This is a pure function with no side effects.
"""

import structlog

logger = structlog.get_logger(__name__)


def build_search_query(article: str, question: str, intent: str | None = None) -> str:
    """Build search query deterministically from inputs.
    
    This function combines article, question, and intent into a search query
    without calling any LLM. The strategy is simple concatenation with structure.
    
    Args:
        article: Original article text
        question: User's question
        intent: Optional intent from LLM analysis
        
    Returns:
        Constructed search query string
        
    Note: This is deterministic - same inputs always produce same output.
    """
    # Use first 300 chars of article as context (avoid token limits)
    article_context = article[:300]
    if len(article) > 300:
        article_context += "..."
    
    # Build query with clear structure
    query_parts = []
    
    # Intent comes first (most important for semantic search)
    if intent:
        query_parts.append(f"Intent: {intent}")
    
    # Question (what user is looking for)
    query_parts.append(f"Question: {question}")
    
    # Article context (background information)
    query_parts.append(f"Context: {article_context}")
    
    query = "\n\n".join(query_parts)
    
    logger.debug("query_built",
                query_length=len(query),
                has_intent=bool(intent),
                article_length=len(article))
    
    return query


def build_search_query_simple(article: str, question: str, intent: str | None = None) -> str:
    """Build simple search query (alternative strategy).
    
    Even simpler approach - just combine key elements.
    
    Args:
        article: Original article text
        question: User's question
        intent: Optional intent from LLM analysis
        
    Returns:
        Simple search query string
    """
    if intent:
        return f"{intent} {question}"
    return question

