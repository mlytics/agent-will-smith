"""LLM client for Databricks LLM endpoint.

Generic injectable client for LLM interactions with dependency injection support.
Shared across all agents that need LLM capabilities.
"""

from databricks_langchain import ChatDatabricks
from langchain.messages import AIMessage
from langchain_core.messages.base import BaseMessage
import structlog

from agent_will_smith.core.exceptions import UpstreamError, UpstreamTimeoutError


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

        Raises:
            UpstreamTimeoutError: If the LLM request times out
            UpstreamError: If the LLM service fails
        """
        try:
            return self._llm.invoke(messages)
        except TimeoutError as e:
            raise UpstreamTimeoutError(
                "LLM request timed out",
                details={
                    "provider": "databricks_llm",
                    "operation": "chat_completion",
                    "endpoint": self.endpoint,
                }
            ) from e
        except Exception as e:
            raise UpstreamError(
                "LLM service failed",
                details={
                    "provider": "databricks_llm",
                    "operation": "chat_completion",
                    "endpoint": self.endpoint,
                    "error": str(e),
                    "error_type": type(e).__name__,
                }
            ) from e
