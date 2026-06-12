from __future__ import annotations

import time
from collections import OrderedDict
from itertools import count
from typing import Any

from packages.auth.models import AuthToken, UserProjectContext


class InvalidAuthTokenError(ValueError):
    pass


class AuthTokenService:
    """Authentication token service with optional TTL and capacity bounds.

    Args:
        max_tokens: Maximum number of concurrent tokens. When exceeded,
            the oldest token is evicted (LRU). None means unbounded.
        ttl_seconds: Time-to-live for tokens in seconds. Expired tokens
            are rejected on verify. None means no expiry.
    """

    def __init__(
        self,
        *,
        max_tokens: int | None = None,
        ttl_seconds: float | None = None,
    ) -> None:
        self._counter = count(1)
        self._max_tokens = max_tokens
        self._ttl_seconds = ttl_seconds
        # OrderedDict preserves insertion order for LRU eviction
        self._tokens: OrderedDict[str, tuple[float, UserProjectContext]] = OrderedDict()

    def issue_token(
        self,
        *,
        user_id: str,
        project_id: str,
        role: str = "builder",
    ) -> AuthToken:
        token = f"nb_test_{user_id}_{project_id}_{next(self._counter)}"
        return self.register_token(token=token, user_id=user_id, project_id=project_id, role=role)

    def register_token(
        self,
        *,
        token: str,
        user_id: str,
        project_id: str,
        role: str = "builder",
    ) -> AuthToken:
        context = UserProjectContext(
            user_id=user_id,
            project_id=project_id,
            role=role,
        )
        normalized = token.strip()
        if not normalized:
            raise ValueError("auth token is required")
        now = time.monotonic()
        self._tokens[normalized] = (now, context)
        # Move to end (most recently used)
        self._tokens.move_to_end(normalized)
        self._evict_if_needed()
        return AuthToken(token=normalized, context=context)

    def verify_token(self, token: str) -> UserProjectContext:
        entry = self._tokens.get(token)
        if entry is None:
            raise InvalidAuthTokenError("invalid auth token")
        issued_at, context = entry
        if self._ttl_seconds is not None:
            age = time.monotonic() - issued_at
            if age > self._ttl_seconds:
                del self._tokens[token]
                raise InvalidAuthTokenError("auth token expired")
        # Touch for LRU ordering
        self._tokens.move_to_end(token)
        return context

    def revoke_token(self, token: str) -> None:
        self._tokens.pop(token, None)

    def _evict_if_needed(self) -> None:
        if self._max_tokens is not None:
            while len(self._tokens) > self._max_tokens:
                # Evict oldest (first inserted)
                self._tokens.popitem(last=False)
