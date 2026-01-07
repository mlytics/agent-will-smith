"""Agent module for product recommendation.

Exports the main agent class and DI container for use in API routes.

Structure:
- product_recommendation/: Product recommendation agent module
  - agent.py: Main agent class (LangGraph)
  - container.py: DI Container (dependency_injector)
  - core/: ExecutionContext, Logger
  - config/: Agent-specific configuration
  - node/: LangGraph nodes (intent, search, composer)
  - infra/: Infrastructure (vector search, LLM client, prompts)
  - schemas/: State and DTOs
"""

from src.agent.product_recommendation.agent import Agent
from src.agent.product_recommendation.container import Container

__all__ = ["Agent", "Container"]
