"""Infrastructure container for shared clients.

Provides generic infrastructure clients that can be used by any agent.
Product-specific logic lives in agent repository layers.
"""

from dependency_injector import containers, providers

from agent_will_smith.core.container import Container as CoreContainer
from agent_will_smith.infra.llm_client import LLMClient
from agent_will_smith.infra.vector_search_client import VectorSearchClient
from agent_will_smith.infra.prompt_client import PromptClient


class Container(containers.DeclarativeContainer):
    """Infrastructure container for shared clients.

    Provides generic infrastructure clients that can be used
    by any agent. Product-specific logic lives in agent repos.

    Usage:
        agent_container references this container and provides
        agent-specific configuration (endpoint names, etc.)
    """

    # Reference core configs
    core_container = providers.Container(CoreContainer)

    # Factory for VectorSearchClient - agents provide endpoint_name
    vector_search_client = providers.Factory(
        VectorSearchClient,
        workspace_url=core_container.databricks_config.provided.host,
        client_id=core_container.databricks_config.provided.client_id,
        client_secret=core_container.databricks_config.provided.client_secret,
        # endpoint_name provided by agent container
    )

    # Factory for LLMClient - agents provide endpoint and params
    llm_client = providers.Factory(
        LLMClient,
        # endpoint, temperature, max_tokens provided by agent container
    )

    # Factory for PromptClient - agents can provide their own cache_ttl
    prompt_client = providers.Factory(
        PromptClient,
        # prompt_cache_ttl provided by agent container
    )
