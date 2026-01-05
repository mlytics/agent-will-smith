"""Dependency injection container for product recommendation agent.

Uses dependency_injector for declarative DI following the joke_agent pattern.
"""

from dependency_injector import containers, providers
import structlog

from core.container import CoreContainer
from agent.product_recommendation.config import agent_config
from agent.product_recommendation.infra.llm_client import LLMClient
from agent.product_recommendation.infra.vector_search import VectorSearchClient
from agent.product_recommendation.node.intent_analysis_node import IntentAnalysisNode
from agent.product_recommendation.node.parallel_search_node import ParallelSearchNode
from agent.product_recommendation.node.compose_response_node import ComposeResponseNode
from agent.product_recommendation.product_recommendation_agent import ProductRecommendationAgent


class Container(containers.DeclarativeContainer):
    """Dependency injection container for product recommendation agent.

    Follows the joke_agent pattern with layered dependencies:
    1. Core (Logger)
    2. Infrastructure (LLMClient, VectorSearchClient)
    3. Nodes (IntentAnalysisNode, ParallelSearchNode, ComposeResponseNode)
    4. Agent (ProductRecommendationAgent)
    """

    core = providers.Container(CoreContainer)

    # Logger
    # We use a Factory provider so that each injection gets a bound logger
    # that respects the current context processing pipeline.
    logger: providers.Provider[structlog.BoundLogger] = providers.Factory(
        structlog.get_logger,
    )

    # Infrastructure layer - LLM client
    llm_client: providers.Provider[LLMClient] = providers.Singleton(
        LLMClient,
        endpoint=agent_config.llm_endpoint,
        temperature=agent_config.llm_temperature,
        max_tokens=agent_config.llm_max_tokens or 300,
        logger=logger,
    )

    # Infrastructure layer - Vector search client
    vector_client: providers.Provider[VectorSearchClient] = providers.Singleton(
        VectorSearchClient,
        workspace_url=core.databricks_config.provided.databricks_host,
        client_id=core.databricks_config.provided.databricks_client_id,
        client_secret=core.databricks_config.provided.databricks_client_secret,
        endpoint_name=agent_config.vector_search_endpoint,
        logger=logger,
    )

    # Node layer - Intent analysis
    intent_analysis_node: providers.Provider[IntentAnalysisNode] = providers.Singleton(
        IntentAnalysisNode,
        llm_client=llm_client,
        logger=logger,
    )

    # Node layer - Parallel search
    parallel_search_node: providers.Provider[ParallelSearchNode] = providers.Singleton(
        ParallelSearchNode,
        vector_client=vector_client,
        logger=logger,
    )

    # Node layer - Compose response
    compose_response_node: providers.Provider[ComposeResponseNode] = providers.Singleton(
        ComposeResponseNode,
        logger=logger,
    )

    # Agent layer - Product recommendation agent (Factory for flexibility)
    agent: providers.Provider[ProductRecommendationAgent] = providers.Factory(
        ProductRecommendationAgent,
        intent_analysis_node=intent_analysis_node,
        parallel_search_node=parallel_search_node,
        compose_response_node=compose_response_node,
        logger=logger,
    )
