import pytest

from packages.auth import AuthTokenService, InvalidAuthTokenError


def test_issue_and_verify_token_returns_user_project_context() -> None:
    service = AuthTokenService()

    token = service.issue_token(
        user_id="user_123",
        project_id="project_alpha",
        role="builder",
    )
    context = service.verify_token(token.token)

    assert context.user_id == "user_123"
    assert context.project_id == "project_alpha"
    assert context.role == "builder"


def test_rejects_unknown_token() -> None:
    service = AuthTokenService()

    with pytest.raises(InvalidAuthTokenError, match="invalid auth token"):
        service.verify_token("missing-token")


def test_tokens_preserve_explicit_project_identity() -> None:
    service = AuthTokenService()

    alpha = service.issue_token(user_id="user_123", project_id="alpha")
    beta = service.issue_token(user_id="user_123", project_id="beta")

    assert service.verify_token(alpha.token).project_id == "alpha"
    assert service.verify_token(beta.token).project_id == "beta"
    assert alpha.token != beta.token
