"""Product recommendation agent configuration.

Agent-specific settings for LLM, vector search, prompts, and behavior.
"""

from agent.product_recommendation.config.settings import ProductRecommendationAgentConfig

# Global agent config instance
agent_config = ProductRecommendationAgentConfig()

__all__ = ["agent_config", "ProductRecommendationAgentConfig"]
