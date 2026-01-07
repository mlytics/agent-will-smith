"""Dependency injection container for product recommendation agent.

Uses dependency_injector for declarative DI following the joke_agent pattern.
"""

from dependency_injector import containers, providers

from src.core.container import Container
from src.agent.product_recommendation.config import ProductRecommendationAgentConfig
from src.agent.product_recommendation.infra.llm_client import LLMClient
from src.agent.product_recommendation.infra.vector_search import VectorSearchClient
from src.agent.product_recommendation.node.query_builder import QueryBuilder
from src.agent.product_recommendation.node.intent_analysis_node import IntentAnalysisNode
from src.agent.product_recommendation.node.parallel_search_node import ParallelSearchNode
from src.agent.product_recommendation.node.compose_response_node import ComposeResponseNode
from src.agent.product_recommendation.agent import Agent


class Container(containers.DeclarativeContainer):
    """Dependency injection container for product recommendation agent.

    Follows the joke_agent pattern with layered dependencies:
    1. Infrastructure (LLMClient, VectorSearchClient)
    2. Nodes (IntentAnalysisNode, ParallelSearchNode, ComposeResponseNode)
    3. Agent (Agent)
    """

    core = providers.Container(Container)

    # Agent Configuration
    agent_config: providers.Provider[ProductRecommendationAgentConfig] = providers.Singleton(
        ProductRecommendationAgentConfig
    )

    # Query Builder
    query_builder: providers.Provider[QueryBuilder] = providers.Factory(
        QueryBuilder,
    )

    # Infrastructure layer - LLM client
    llm_client: providers.Provider[LLMClient] = providers.Singleton(
        LLMClient,
        endpoint=agent_config.provided.llm_endpoint,
        temperature=agent_config.provided.llm_temperature,
        max_tokens=agent_config.provided.llm_max_tokens,
    )

    # Infrastructure layer - Vector search client
    vector_client: providers.Provider[VectorSearchClient] = providers.Singleton(
        VectorSearchClient,
        workspace_url=core.databricks_config.provided.databricks_host,
        client_id=core.databricks_config.provided.databricks_client_id,
        client_secret=core.databricks_config.provided.databricks_client_secret,
        endpoint_name=agent_config.provided.vector_search_endpoint,
    )

    # Node layer - Intent analysis
    intent_analysis_node: providers.Provider[IntentAnalysisNode] = providers.Singleton(
        IntentAnalysisNode,
        llm_client=llm_client,
    )

    # Node layer - Parallel search
    parallel_search_node: providers.Provider[ParallelSearchNode] = providers.Singleton(
        ParallelSearchNode,
        vector_client=vector_client,
        query_builder=query_builder,
        agent_config=agent_config,
    )

    # Node layer - Compose response
    compose_response_node: providers.Provider[ComposeResponseNode] = providers.Singleton(
        ComposeResponseNode,
    )

    # Agent layer - Product recommendation agent (Factory for flexibility)
    agent: providers.Provider[Agent] = providers.Factory(
        Agent,
        intent_analysis_node=intent_analysis_node,
        parallel_search_node=parallel_search_node,
        compose_response_node=compose_response_node,
    )
