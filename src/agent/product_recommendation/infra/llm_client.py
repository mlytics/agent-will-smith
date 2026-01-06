"""LLM client for Databricks LLM endpoint.

Injectable client class for LLM interactions with dependency injection support.
"""

from databricks_langchain import ChatDatabricks
import structlog


class LLMClient:
    """Client class for LLM interactions with dependency injection support.

    This replaces the global singleton pattern with an injectable class.
    The DI container manages the lifecycle as a singleton.
    """

    def __init__(
        self,
        endpoint: str,
        temperature: float,
        max_tokens: int,
        logger: structlog.BoundLogger,
    ):
        """Initialize LLM client with configuration.

        Args:
            endpoint: The Databricks model endpoint to use
            temperature: Temperature for generation
            max_tokens: Maximum tokens for generation
            logger: Structlog logger with bound context
        """
        self.endpoint = endpoint
        self.logger = logger
        self._llm = ChatDatabricks(
            endpoint=endpoint,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        self.logger.info("llm_client_initialized", endpoint=endpoint)
        
    def invoke_with_messages(self, messages: list[dict]) -> str:
        """Invoke the LLM with a list of messages.

        Args:
            messages: List of message dicts with 'role' and 'content' keys

        Returns:
            The generated text response

        Raises:
            Various exceptions from LangChain (TimeoutError, etc.)
        """
        self.logger.info("llm_invoke_messages", message_count=len(messages))
        response = self._llm.invoke(messages)
        self.logger.info("llm_response", response_length=len(response.content))
        return response.content.strip()
