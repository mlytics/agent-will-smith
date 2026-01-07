"""Dependency injection container for product recommendation agent.

Uses dependency_injector for declarative DI following the joke_agent pattern.
"""

from dependency_injector import containers, providers

from agent_will_smith.core.container import Container as CoreContainer
from agent_will_smith.infra.container import Container as InfraContainer
from agent_will_smith.agent.product_recommendation.config import ProductRecommendationAgentConfig
from agent_will_smith.agent.product_recommendation.repo.product_vector_repository import ProductVectorRepository
from agent_will_smith.agent.product_recommendation.node.query_builder import QueryBuilder
from agent_will_smith.agent.product_recommendation.node.intent_analysis_node import IntentAnalysisNode
from agent_will_smith.agent.product_recommendation.node.parallel_search_node import ParallelSearchNode
from agent_will_smith.agent.product_recommendation.node.compose_response_node import ComposeResponseNode
from agent_will_smith.agent.product_recommendation.agent import Agent


class Container(containers.DeclarativeContainer):
    """Dependency injection container for product recommendation agent.

    Follows the joke_agent pattern with layered dependencies:
    1. Infrastructure (shared clients from InfraContainer)
    2. Repository (product-specific logic)
    3. Nodes (IntentAnalysisNode, ParallelSearchNode, ComposeResponseNode)
    4. Agent (Agent)
    """

    # Reference containers
    core_container = providers.Container(CoreContainer)
    infra_container = providers.Container(InfraContainer)

    # Agent Configuration
    agent_config: providers.Provider[ProductRecommendationAgentConfig] = providers.Singleton(
        ProductRecommendationAgentConfig
    )

    # Query Builder
    query_builder: providers.Provider[QueryBuilder] = providers.Factory(
        QueryBuilder,
    )

    # Infrastructure layer - instantiate shared clients with agent config
    llm_client = providers.Singleton(
        infra_container.llm_client,
        endpoint=agent_config.provided.llm_endpoint,
        temperature=agent_config.provided.llm_temperature,
        max_tokens=agent_config.provided.llm_max_tokens,
    )

    vector_search_client = providers.Singleton(
        infra_container.vector_search_client,
        endpoint_name=agent_config.provided.vector_search_endpoint,
    )

    prompt_client = providers.Factory(
        infra_container.prompt_client,
        prompt_cache_ttl=agent_config.provided.prompt_cache_ttl,
    )

    # Repository layer - product-specific logic
    product_vector_repo: providers.Provider[ProductVectorRepository] = providers.Singleton(
        ProductVectorRepository,
        vector_client=vector_search_client,
        config=agent_config,
    )

    # Node layer - Intent analysis
    intent_analysis_node: providers.Provider[IntentAnalysisNode] = providers.Singleton(
        IntentAnalysisNode,
        llm_client=llm_client,
        prompt_client=prompt_client,
        config=agent_config,
    )

    # Node layer - Parallel search
    parallel_search_node: providers.Provider[ParallelSearchNode] = providers.Singleton(
        ParallelSearchNode,
        product_repo=product_vector_repo,
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
        agent_config=agent_config,
    )
