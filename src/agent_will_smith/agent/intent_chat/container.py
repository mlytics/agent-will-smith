"""Dependency injection container for intent chat agent.

Uses dependency_injector for declarative DI following the product_recommendation pattern.
"""

from dependency_injector import containers, providers

from agent_will_smith.core.container import Container as CoreContainer
from agent_will_smith.infra.container import Container as InfraContainer
from agent_will_smith.agent.intent_chat.config import Config
from agent_will_smith.agent.intent_chat.node.conversation_node import ConversationNode
from agent_will_smith.agent.intent_chat.node.tool_calling_node import ToolCallingNode
from agent_will_smith.agent.intent_chat.node.tool_execution_node import ToolExecutionNode
from agent_will_smith.agent.intent_chat.node.response_node import ResponseNode
from agent_will_smith.agent.intent_chat.agent import Agent
from agent_will_smith.conversation_analytics.database import ConversationDatabase
from agent_will_smith.conversation_analytics.logger import ConversationLogger


class Container(containers.DeclarativeContainer):
    """Dependency injection container for intent chat agent.

    Follows the product_recommendation pattern with layered dependencies:
    1. Infrastructure (shared clients from InfraContainer)
    2. Nodes (ConversationNode, ToolCallingNode, ToolExecutionNode, ResponseNode)
    3. Agent (Agent)
    """

    # Reference containers
    core_container = providers.Container(CoreContainer)
    infra_container = providers.Container(InfraContainer)

    # Agent Configuration
    agent_config: providers.Provider[Config] = providers.Singleton(
        Config
    )

    # Infrastructure layer - instantiate shared clients with agent config
    llm_client = providers.Singleton(
        infra_container.llm_client,
        endpoint=agent_config.provided.llm_endpoint,
        temperature=agent_config.provided.llm_temperature,
        max_tokens=agent_config.provided.llm_max_tokens,
    )

    prompt_client = providers.Factory(
        infra_container.prompt_client,
        prompt_cache_ttl=agent_config.provided.prompt_cache_ttl,
    )

    # Node layer - Conversation node
    conversation_node: providers.Provider[ConversationNode] = providers.Singleton(
        ConversationNode,
    )

    # Node layer - Tool calling node
    tool_calling_node: providers.Provider[ToolCallingNode] = providers.Singleton(
        ToolCallingNode,
        llm_client=llm_client,
        prompt_client=prompt_client,
        config=agent_config,
    )

    # Node layer - Tool execution node
    tool_execution_node: providers.Provider[ToolExecutionNode] = providers.Singleton(
        ToolExecutionNode,
        config=agent_config,
    )

    # Node layer - Response node
    response_node: providers.Provider[ResponseNode] = providers.Singleton(
        ResponseNode,
    )

    # Conversation analytics
    conversation_database: providers.Provider[ConversationDatabase] = providers.Singleton(
        ConversationDatabase,
        db_path=agent_config.provided.analytics_db_path,
    )

    conversation_logger: providers.Provider[ConversationLogger] = providers.Singleton(
        ConversationLogger,
        database=conversation_database,
    )

    # Agent layer - Intent chat agent (Factory for flexibility)
    agent: providers.Provider[Agent] = providers.Factory(
        Agent,
        conversation_node=conversation_node,
        tool_calling_node=tool_calling_node,
        tool_execution_node=tool_execution_node,
        response_node=response_node,
        agent_config=agent_config,
        conversation_logger=conversation_logger,
    )
