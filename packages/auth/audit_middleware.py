"""Audit middleware and request ID middleware for FastAPI.

AuditMiddleware logs every mutation request (POST, PUT, DELETE, PATCH)
to an audit writer function. GET and HEAD requests are not audited.

RequestIdMiddleware adds a unique X-Request-ID header to every response.
If the client sends an X-Request-ID, it is preserved.
"""
from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Callable

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from packages.auth.service import AuthTokenService, InvalidAuthTokenError

logger = logging.getLogger(__name__)

# Methods considered mutations (trigger audit logging)
_MUTATION_METHODS = {"POST", "PUT", "DELETE", "PATCH"}

# Path prefixes that are never audited (health checks, static files)
_SKIP_PREFIXES = ("/health", "/static", "/favicon")


class AuditMiddleware(BaseHTTPMiddleware):
    """Middleware that logs mutation requests to an audit writer.

    Args:
        app: ASGI application.
        audit_writer: Callable that receives a dict with audit event fields.
            Signature: audit_writer(event: dict) -> None
    """

    def __init__(self, app: Any, audit_writer: Callable[[dict], None] | None = None) -> None:
        super().__init__(app)
        self._audit_writer = audit_writer or _default_audit_writer

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        response = await call_next(request)

        if self._should_audit(request):
            event = self._build_event(request, response)
            try:
                self._audit_writer(event)
            except Exception as exc:
                logger.error("audit_write_failed error=%s event=%s", exc, event.get("request_id"))
                if 200 <= response.status_code < 400:
                    return JSONResponse(
                        {
                            "error": "audit_write_failed",
                            "details": "Mutation audit event could not be persisted",
                        },
                        status_code=500,
                    )

        return response

    def _should_audit(self, request: Request) -> bool:
        """Determine if this request should generate an audit event."""
        if request.method not in _MUTATION_METHODS:
            return False
        path = request.url.path
        for prefix in _SKIP_PREFIXES:
            if path.startswith(prefix):
                return False
        return True

    def _build_event(self, request: Request, response: Response) -> dict:
        """Build audit event dict from request and response."""
        request_id = (
            getattr(request.state, "request_id", None)
            or request.headers.get("x-request-id")
            or response.headers.get("x-request-id")
            or str(uuid.uuid4())
        )
        return {
            "request_id": request_id,
            "route": request.url.path,
            "method": request.method,
            "status_code": response.status_code,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "actor_id": getattr(request.state, "actor_id", None) or "unauthenticated",
            "project_id": getattr(request.state, "project_id", None) or "unknown",
            "resource_type": _extract_resource_type(request.url.path),
            "resource_id": _extract_resource_id(request.url.path),
        }


class AuthContextMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: Any, auth_token_service: AuthTokenService) -> None:
        super().__init__(app)
        self._auth_token_service = auth_token_service

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        request.state.actor_id = "unauthenticated"
        request.state.project_id = "unknown"
        authorization = request.headers.get("authorization")
        if authorization is not None:
            scheme, _, token = authorization.partition(" ")
            if scheme.lower() == "bearer" and token.strip():
                try:
                    context = self._auth_token_service.verify_token(token.strip())
                except InvalidAuthTokenError:
                    return await call_next(request)
                request.state.actor_id = context.user_id
                request.state.project_id = context.project_id
                request.state.role = context.role
        return await call_next(request)


class RequestIdMiddleware(BaseHTTPMiddleware):
    """Middleware that adds X-Request-ID to every response.

    If the client provides an X-Request-ID header, it is preserved.
    Otherwise, a new UUID is generated.
    """

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        request_id = request.headers.get("x-request-id") or str(uuid.uuid4())
        request.state.request_id = request_id
        response = await call_next(request)
        response.headers["x-request-id"] = request_id
        return response


def _default_audit_writer(event: dict) -> None:
    """Default audit writer that logs the event."""
    logger.info(
        "audit_event request_id=%s method=%s route=%s status=%s",
        event.get("request_id"),
        event.get("method"),
        event.get("route"),
        event.get("status_code"),
    )


def _extract_resource_type(path: str) -> str:
    """Extract resource type from URL path.

    /api/strategies/123 -> strategies
    /api/promotions/abc -> promotions
    """
    parts = path.strip("/").split("/")
    # /api/{resource_type}/{resource_id}...
    if len(parts) >= 2 and parts[0] == "api":
        return parts[1]
    return path


def _extract_resource_id(path: str) -> str | None:
    """Extract resource ID from URL path if present."""
    parts = path.strip("/").split("/")
    if len(parts) >= 3 and parts[0] == "api":
        return parts[2]
    return None
