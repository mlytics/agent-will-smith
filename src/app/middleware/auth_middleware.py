"""Authentication middleware for Bearer token validation.

Follows guideline: "Keep business rules out of prompts" - auth logic in code, not prompts.
"""

from typing import List, Optional
from fastapi import Request, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from dependency_injector.wiring import inject, Provide

from src.core.core_container import CoreContainer


class AuthMiddleware(BaseHTTPMiddleware):
    """Authentication middleware using Dependency Injection.

    Enforces Bearer token authentication on all routes except excluded ones.
    """

    @inject
    def __init__(
        self,
        app,
        excluded_paths: Optional[List[str]] = None,
        api_key: str = Provide[CoreContainer.fastapi_config.provided.api_key],
    ):
        """Initialize middleware with injected API key and excluded paths."""
        super().__init__(app)
        self.api_key = api_key
        self.excluded_paths = excluded_paths or []

    async def dispatch(self, request: Request, call_next):
        """Process request and verify API key if not excluded."""
        # 1. Check if path is excluded (bypass)
        if request.url.path in self.excluded_paths:
            return await call_next(request)

        # 2. Also bypass documentation routes if not explicitly blocked
        # (Usually desirable to keep docs public or separate, adjusting as needed)
        if request.url.path in ["/docs", "/redoc", "/openapi.json"]:
            return await call_next(request)

        # 3. Verify Authentication
        auth_header = request.headers.get("Authorization")

        if not auth_header or not auth_header.startswith("Bearer "):
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": "Missing or invalid Authorization header"},
                headers={"WWW-Authenticate": "Bearer"},
            )

        token = auth_header.split(" ")[1]
        if token != self.api_key:
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": "Invalid API key"},
                headers={"WWW-Authenticate": "Bearer"},
            )

        return await call_next(request)
