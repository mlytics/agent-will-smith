"""Authentication middleware for Bearer token validation.

Follows guideline: "Keep business rules out of prompts" - auth logic in code, not prompts.
"""

from typing import Annotated
from fastapi import HTTPException, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from core.config import config

# Bearer token security scheme
security = HTTPBearer()


async def verify_api_key(
    credentials: Annotated[HTTPAuthorizationCredentials, Security(security)]
) -> str:
    """Verify Bearer token against configured API key.

    Args:
        credentials: HTTP authorization credentials from request header

    Returns:
        The API key if valid

    Raises:
        HTTPException: If token is invalid (401 Unauthorized)
    """
    if credentials.credentials != config.api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return credentials.credentials

