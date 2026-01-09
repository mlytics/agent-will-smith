"""Authentication middleware for x-api-key header validation (pure ASGI)."""

from __future__ import annotations

from typing import Iterable, Optional
from fastapi import status
from starlette.responses import JSONResponse
from dependency_injector.wiring import inject, Provide
from starlette.datastructures import Headers

from agent_will_smith.core.container import Container

class AuthMiddleware:
    """Authentication middleware using Dependency Injection (pure ASGI).

    Enforces x-api-key authentication on all HTTP routes except excluded ones.
    """

    @inject
    def __init__(
        self,
        app,
        excluded_paths: Optional[Iterable[str]] = None,
        api_key: str = Provide[Container.fastapi_config.provided.api_key],
    ):
        self.app = app
        self.api_key = api_key
        self.excluded_paths = set(excluded_paths or [])

    async def __call__(self, scope, receive, send):
        path = scope.get("path") or ""
        if path in self.excluded_paths:
            await self.app(scope, receive, send)
            return

        headers = Headers(scope=scope)
        api_key = headers.get("x-api-key")

        if not api_key:
            res = JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": "Missing x-api-key header"},
            )
            await res(scope, receive, send)
            return

        if api_key != self.api_key:
            res = JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": "Invalid API key"},
            )
            await res(scope, receive, send)
            return

        await self.app(scope, receive, send)