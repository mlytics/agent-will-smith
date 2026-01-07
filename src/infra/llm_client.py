"""LLM client for Databricks LLM endpoint.

Generic injectable client for LLM interactions with dependency injection support.
Shared across all agents that need LLM capabilities.
"""

from databricks_langchain import ChatDatabricks
from langchain.messages import AIMessage
from langchain_core.messages.base import BaseMessage
import structlog


class LLMClient:
    """Generic client for LLM interactions with dependency injection support.

    This replaces the global singleton pattern with an injectable class.
    The DI container manages the lifecycle as a singleton.
    Fully generic - can be used by any agent.
    """

    def __init__(
        self,
        endpoint: str,
        temperature: float,
        max_tokens: int,
    ):
        """Initialize LLM client with configuration.

        Args:
            endpoint: The Databricks model endpoint to use
            temperature: Temperature for generation
            max_tokens: Maximum tokens for generation
        """
        self.endpoint = endpoint
        self.logger = structlog.get_logger(__name__)
        self._llm = ChatDatabricks(
            endpoint=endpoint,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        self.logger.info("llm client initialized", endpoint=endpoint)

    def invoke(self, messages: list[BaseMessage]) -> AIMessage:
        """Invoke the LLM with a list of LangChain messages.

        Args:
            messages: List of LangChain message types (SystemMessage, HumanMessage, etc.)

        Returns:
            The generated AIMessage
        """
        return self._llm.invoke(messages)
