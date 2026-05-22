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
        context = UserProjectContext(
            user_id=user_id,
            project_id=project_id,
            role=role,
        )
        token = f"nb_test_{user_id}_{project_id}_{next(self._counter)}"
        self._tokens[token] = context
        return AuthToken(token=token, context=context)

    def verify_token(self, token: str) -> UserProjectContext:
        context = self._tokens.get(token)
        if context is None:
            raise InvalidAuthTokenError("invalid auth token")
        return context
