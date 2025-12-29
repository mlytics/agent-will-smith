"""Agent module for product recommendation.

Exports the main agent function for use in API routes.

Structure:
- product_recommendation/: Product recommendation agent module
  - agent.py: Main agent orchestration
  - config/: Agent-specific configuration
  - node/: LangGraph nodes (future)
  - infra/: Infrastructure (vector search, prompts)
  - schemas.py: State and DTOs
  - scorers.py: MLflow evaluation scorers
"""

from agent.product_recommendation.agent import recommend_products

__all__ = ["recommend_products"]

