"""Authentication middleware for Bearer token validation.

Follows guideline: "Keep business rules out of prompts" - auth logic in code, not prompts.
"""

from typing import Annotated
from fastapi import HTTPException, Security, status, Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from dependency_injector.wiring import inject, Provide

from core.container import CoreContainer

# Bearer token security scheme
security = HTTPBearer()


@inject
async def verify_api_key(
    credentials: Annotated[HTTPAuthorizationCredentials, Security(security)],
    api_key: str = Depends(Provide[CoreContainer.fastapi_config.provided.api_key]),
) -> str:
    """Verify Bearer token against configured API key.

    Args:
        credentials: HTTP authorization credentials from request header

    Returns:
        The API key if valid

    Raises:
        HTTPException: If token is invalid (401 Unauthorized)
    """
    if credentials.credentials != api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return credentials.credentials
