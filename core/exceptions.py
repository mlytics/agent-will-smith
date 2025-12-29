"""Custom exceptions with HTTP status code mapping.

This module provides a hierarchy of exceptions for agent errors
with explicit HTTP status code mappings for API layer.

To be fully implemented in Commit 3.
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


# Placeholder exceptions - will be fully implemented in Commit 3
class IntentAnalysisError(AgentException):
    """Intent analysis failed."""
    status_code = 422
    message = "Failed to analyze intent"


class VectorSearchError(AgentException):
    """Vector search service error."""
    status_code = 502
    message = "Vector search service error"


class VectorSearchTimeout(AgentException):
    """Vector search timed out."""
    status_code = 504
    message = "Vector search timed out"


def map_exception_to_http_status(exc: Exception) -> tuple[int, str]:
    """Map exception to HTTP status code and message.
    
    Args:
        exc: Exception to map
        
    Returns:
        (status_code, message) tuple
    """
    if isinstance(exc, AgentException):
        return exc.status_code, exc.message
    return 500, "Internal server error"

