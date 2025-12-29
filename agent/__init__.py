"""Agent module for product recommendation.

Exports the main agent function for use in API routes.

Structure:
- product_recommendation_agent.py: Current working agent (will be refactored)
- product_recommendation_agent/: New LangGraph structure (being built)
"""

from agent.product_recommendation_agent import recommend_products

__all__ = ["recommend_products"]

