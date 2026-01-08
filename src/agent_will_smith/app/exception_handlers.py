"""FastAPI exception handlers for application-wide error handling.

Maps domain exceptions to appropriate HTTP responses with structured logging.
Centralizes exception-to-HTTP-response logic separate from application bootstrap.
"""

from fastapi import Request
from fastapi.responses import JSONResponse
import structlog

from agent_will_smith.core.exceptions import (
    AgentException,
    BadRequestError,
    DomainValidationError,
    UnauthorizedError,
    ForbiddenError,
    NotFoundError,
    ConflictError,
    RateLimitedError,
    AgentStateError,
    ToolExecutionError,
    AgentTimeoutError,
    AgentCancelledError,
    UpstreamError,
    UpstreamTimeoutError,
    UpstreamRateLimitError,
    PromptLoadError,
    NoResultsFoundError,
)


def map_agent_exception_to_status(exc: AgentException) -> int:
    """Map AgentException to HTTP status code.
    
    Args:
        exc: The AgentException instance to map
        
    Returns:
        HTTP status code (4xx for client errors, 5xx for server errors)
    """
    # Client errors (4xx)
    if isinstance(exc, BadRequestError):
        return 400
    if isinstance(exc, UnauthorizedError):
        return 401
    if isinstance(exc, ForbiddenError):
        return 403
    if isinstance(exc, (NotFoundError, NoResultsFoundError)):
        return 404
    if isinstance(exc, AgentCancelledError):
        return 408
    if isinstance(exc, ConflictError):
        return 409
    if isinstance(exc, DomainValidationError):
        return 422
    if isinstance(exc, (RateLimitedError, UpstreamRateLimitError)):
        return 429

    # Agent state errors (context-dependent)
    if isinstance(exc, AgentStateError):
        return 409 if exc.conflict else 500

    # Agent runtime errors
    if isinstance(exc, AgentTimeoutError):
        return 504
    if isinstance(exc, ToolExecutionError):
        return 502 if exc.details.get("is_external", False) else 500

    # Upstream errors (5xx)
    if isinstance(exc, (UpstreamError, PromptLoadError)):
        return 502
    if isinstance(exc, UpstreamTimeoutError):
        return 504

    # Fallback
    return 500


async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Global exception handler - maps all exceptions to HTTP responses.
    
    Handles:
    - Custom AgentException hierarchy with domain-specific mappings
    - Standard Python exceptions (ValueError, KeyError, TimeoutError)
    - Unknown exceptions with fallback 500 response
    
    Provides structured logging with trace IDs for all errors.
    
    Args:
        request: FastAPI request object
        exc: The exception that was raised
        
    Returns:
        JSONResponse with error details and appropriate status code
    """
    logger = structlog.get_logger(__name__)
    trace_id = getattr(request.state, "trace_id", "unknown")

    # Determine status code and error details
    if isinstance(exc, AgentException):
        status_code = map_agent_exception_to_status(exc)
        error_message = exc.message
        error_details = exc.details
    elif isinstance(exc, ValueError):
        status_code = 400
        error_message = f"Invalid value: {str(exc)}"
        error_details = {}
    elif isinstance(exc, KeyError):
        status_code = 400
        error_message = f"Missing required field: {str(exc)}"
        error_details = {}
    elif isinstance(exc, TimeoutError):
        status_code = 504
        error_message = "Request timed out"
        error_details = {}
    else:
        # Unknown exceptions
        status_code = 500
        error_message = "Internal server error"
        error_details = {}

    # Log with full context
    logger.error(
        "exception handled",
        trace_id=trace_id,
        status_code=status_code,
        error_type=type(exc).__name__,
        error_message=error_message,
        error_details=error_details,
        exc_info=exc,
    )

    # Return JSON response
    response_body = {
        "error": error_message,
        "trace_id": trace_id,
        "details": error_details if error_details else None,
    }

    return JSONResponse(
        status_code=status_code,
        content=response_body,
    )


def register_exception_handlers(app) -> None:
    """Register all exception handlers with the FastAPI application.
    
    Args:
        app: FastAPI application instance
    """
    app.exception_handler(Exception)(global_exception_handler)
