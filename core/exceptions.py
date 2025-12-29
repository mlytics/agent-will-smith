"""Custom exceptions with HTTP status code mapping.

This module provides a hierarchy of exceptions for agent errors
with explicit HTTP status code mappings for API layer.

Follows architecture principle: "Exceptions should be mapped to HTTP Status Code"
at the API layer (single try-catch).
"""


class AgentException(Exception):
    """Base exception for all agent errors.
    
    Attributes:
        status_code: HTTP status code to return
        message: Error message
    """
    status_code: int = 500
    message: str = "Internal agent error"
    
    def __init__(self, message: str | None = None):
        self.message = message or self.message
        super().__init__(self.message)


# Configuration Errors (4xx - Client Issues)
class InvalidConfigurationError(AgentException):
    """Invalid configuration detected."""
    status_code = 500  # Internal server error - config is our responsibility
    message = "Invalid configuration"


class TenantAccessDenied(AgentException):
    """Tenant does not have access to requested resource."""
    status_code = 403
    message = "Access denied to requested vertical"


class InvalidVerticalError(AgentException):
    """Invalid vertical specified in request."""
    status_code = 400
    message = "Invalid vertical specified"


class InvalidInputError(AgentException):
    """Invalid input parameters."""
    status_code = 400
    message = "Invalid input parameters"


# Agent Execution Errors (4xx/5xx)
class IntentAnalysisError(AgentException):
    """Intent analysis failed."""
    status_code = 422  # Unprocessable Entity
    message = "Failed to analyze intent"


class AgentExecutionError(AgentException):
    """Agent execution failed."""
    status_code = 500
    message = "Agent execution failed"


class AgentTimeoutError(AgentException):
    """Agent execution timed out."""
    status_code = 504
    message = "Agent execution timed out"


# External Service Errors (5xx - Upstream Issues)
class VectorSearchError(AgentException):
    """Vector search service error."""
    status_code = 502  # Bad Gateway - upstream service issue
    message = "Vector search service error"


class VectorSearchTimeout(AgentException):
    """Vector search timed out."""
    status_code = 504  # Gateway Timeout
    message = "Vector search timed out"


class VectorSearchIndexNotFound(AgentException):
    """Vector search index not found."""
    status_code = 502  # Bad Gateway - configuration/infrastructure issue
    message = "Vector search index not found"


class LLMServiceError(AgentException):
    """LLM service error."""
    status_code = 502  # Bad Gateway
    message = "LLM service error"


class LLMServiceTimeout(AgentException):
    """LLM service timed out."""
    status_code = 504  # Gateway Timeout
    message = "LLM service timed out"


class PromptLoadError(AgentException):
    """Failed to load prompt from MLflow."""
    status_code = 502  # Bad Gateway - MLflow service issue
    message = "Failed to load prompt from registry"


class NoResultsFoundError(AgentException):
    """No results found for query (not always an error, might be valid)."""
    status_code = 404  # Not Found
    message = "No results found"


def map_exception_to_http_status(exc: Exception) -> tuple[int, str]:
    """Map exception to HTTP status code and message.
    
    This function is used at the API layer (single try-catch) to convert
    domain exceptions into appropriate HTTP responses.
    
    Args:
        exc: Exception to map
        
    Returns:
        (status_code, message) tuple
        
    Examples:
        >>> exc = IntentAnalysisError("Custom message")
        >>> status, msg = map_exception_to_http_status(exc)
        >>> assert status == 422
        >>> assert msg == "Custom message"
    """
    if isinstance(exc, AgentException):
        return exc.status_code, exc.message
    
    # Generic Python exceptions
    if isinstance(exc, ValueError):
        return 400, f"Invalid value: {str(exc)}"
    if isinstance(exc, KeyError):
        return 400, f"Missing required field: {str(exc)}"
    if isinstance(exc, TimeoutError):
        return 504, "Request timed out"
    
    # Unknown exceptions - internal server error
    return 500, "Internal server error"


__all__ = [
    # Base
    "AgentException",
    # Configuration
    "InvalidConfigurationError",
    "TenantAccessDenied",
    "InvalidVerticalError",
    "InvalidInputError",
    # Agent Execution
    "IntentAnalysisError",
    "AgentExecutionError",
    "AgentTimeoutError",
    # External Services
    "VectorSearchError",
    "VectorSearchTimeout",
    "VectorSearchIndexNotFound",
    "LLMServiceError",
    "LLMServiceTimeout",
    "PromptLoadError",
    "NoResultsFoundError",
    # Mapping
    "map_exception_to_http_status",
]

