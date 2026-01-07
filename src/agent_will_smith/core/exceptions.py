"""Custom exceptions for agent errors.

This module provides a hierarchy of exceptions for agent errors
with structured details for debugging.

Exceptions are mapped to HTTP Status Codes at the API layer in main.py
(single global exception handler).
"""


class AgentException(Exception):
    """Base exception for all agent errors.

    Attributes:
        message: Error message
        details: Optional structured details for debugging
    """
    message: str = "Internal agent error"

    def __init__(self, message: str | None = None, details: dict | None = None):
        self.message = message or self.message
        self.details = details or {}
        super().__init__(self.message)


# Client/Request-level Errors (4xx)
class BadRequestError(AgentException):
    """Request shape passes FastAPI validation but semantically wrong."""
    message = "Bad request"


class DomainValidationError(AgentException):
    """Domain constraints violated (prompt too long, unsupported model, etc.)."""
    message = "Domain validation failed"


class UnauthorizedError(AgentException):
    """Authentication failures."""
    message = "Unauthorized"


class ForbiddenError(AgentException):
    """Authorization failures."""
    message = "Forbidden"


class NotFoundError(AgentException):
    """Resource not found."""
    message = "Resource not found"


class ConflictError(AgentException):
    """Concurrency, idempotency collisions, 'already running'."""
    message = "Conflict"


class RateLimitedError(AgentException):
    """Rate limiting (include retry_after in details)."""
    message = "Rate limited"

# Agent/Runtime Errors (LangGraph core)
class AgentStateError(AgentException):
    """Invalid/missing state transitions.

    Use conflict=True for 409 (user-resolvable conflicts like concurrent execution).
    Use conflict=False for 500 (programming errors like invalid state).
    """
    message = "Agent state error"

    def __init__(self, message: str | None = None, details: dict | None = None, conflict: bool = False):
        super().__init__(message, details)
        self.conflict = conflict


class ToolExecutionError(AgentException):
    """Tool execution failed.

    Details should include:
    - tool_name: str
    - tool_call_id: str (optional)
    - provider_request_id: str (optional)
    - is_external: bool (True = 502, False = 500)
    """
    message = "Tool execution failed"


class AgentTimeoutError(AgentException):
    """Agent execution timed out."""
    message = "Agent execution timed out"


class AgentCancelledError(AgentException):
    """User-initiated cancellation."""
    message = "Agent execution cancelled"


# Upstream Service Errors (5xx)
class UpstreamError(AgentException):
    """Generic provider failure.

    Details should include:
    - provider: str (e.g., "databricks_vector_search", "databricks_llm", "mlflow")
    - operation: str (e.g., "similarity_search", "chat_completion", "load_prompt")
    - request_id: str (optional, if provider gives one)
    """
    message = "Upstream service error"


class UpstreamTimeoutError(AgentException):
    """Distinguish timeouts from other provider errors.

    Details should include: provider, operation, timeout_seconds
    """
    message = "Upstream service timeout"


class UpstreamRateLimitError(AgentException):
    """Separate from app rate limit.

    Details should include: provider, retry_after (optional)
    """
    message = "Upstream rate limited"


class PromptLoadError(AgentException):
    """Failed to load prompt from MLflow."""
    message = "Failed to load prompt from registry"


class NoResultsFoundError(AgentException):
    """No results found for query (not always an error, might be valid)."""
    message = "No results found"


__all__ = [
    # Base
    "AgentException",
    # Client/Request (4xx)
    "BadRequestError",
    "DomainValidationError",
    "UnauthorizedError",
    "ForbiddenError",
    "NotFoundError",
    "ConflictError",
    "RateLimitedError",
    # Agent/Runtime
    "AgentStateError",
    "ToolExecutionError",
    "AgentTimeoutError",
    "AgentCancelledError",
    # Upstream (5xx)
    "UpstreamError",
    "UpstreamTimeoutError",
    "UpstreamRateLimitError",
    "PromptLoadError",
    "NoResultsFoundError",
]
