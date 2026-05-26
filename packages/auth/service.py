from __future__ import annotations

from itertools import count

from packages.auth.models import AuthToken, UserProjectContext


class InvalidAuthTokenError(ValueError):
    pass


class AuthTokenService:
    def __init__(self) -> None:
        self._counter = count(1)
        self._tokens: dict[str, UserProjectContext] = {}

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
        self._tokens[normalized] = context
        return AuthToken(token=normalized, context=context)

    def verify_token(self, token: str) -> UserProjectContext:
        context = self._tokens.get(token)
        if context is None:
            raise InvalidAuthTokenError("invalid auth token")
        return context
