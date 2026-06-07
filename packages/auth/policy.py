"""Auth policy: project scope validation, BUILDER_ENV validation, production token enforcement, CORS validation."""
from __future__ import annotations

from enum import Enum

from packages.auth.models import ScopedArtifactRef, UserProjectContext


class ProjectScopeError(PermissionError):
    pass


class BuilderEnvironment(str, Enum):
    LOCAL = "local"
    STAGING = "staging"
    PRODUCTION = "production"


_UNSAFE_DEV_TOKENS = {"dev-token", "test-token", "changeme"}

_MIN_TOKEN_LENGTH = 32


def assert_same_project(context: UserProjectContext, artifact: ScopedArtifactRef) -> None:
    """Assert that the context matches the artifact's user and project scope."""
    if context.user_id != artifact.user_id or context.project_id != artifact.project_id:
        raise ProjectScopeError(
            f"artifact {artifact.artifact_type}/{artifact.artifact_id} is outside user/project scope"
        )


def validate_builder_env(raw: str) -> BuilderEnvironment:
    """Validate and normalize the BUILDER_ENV value."""
    if not raw.strip():
        return BuilderEnvironment.LOCAL
    try:
        return BuilderEnvironment(raw.strip().lower())
    except ValueError:
        raise ValueError(
            f"unknown BUILDER_ENV: '{raw}'. Must be one of: local, staging, production"
        ) from None


def validate_production_token(
    *,
    env: BuilderEnvironment,
    token: str | None,
    public_token: str | None,
) -> None:
    """Validate auth token requirements based on environment."""
    if env == BuilderEnvironment.LOCAL:
        return

    if not token:
        raise ValueError("BUILDER_API_TOKEN is required in staging/production")

    if token in _UNSAFE_DEV_TOKENS:
        raise ValueError(f"'{token}' is forbidden in staging/production")

    if len(token) < _MIN_TOKEN_LENGTH:
        raise ValueError(
            f"BUILDER_API_TOKEN is too short for staging/production "
            f"(got {len(token)} chars, need {_MIN_TOKEN_LENGTH}+)"
        )

    if public_token:
        raise ValueError(
            "NEXT_PUBLIC_BUILDER_API_TOKEN is forbidden in staging/production. "
            "Use server-side auth only."
        )


def validate_cors_config(
    *,
    env: BuilderEnvironment,
    origins: list[str],
) -> None:
    """Validate CORS configuration based on environment."""
    if env == BuilderEnvironment.LOCAL:
        return

    if not origins:
        raise ValueError("CORS origins must not be empty in staging/production")

    if "*" in origins:
        raise ValueError("Wildcard CORS (*) is forbidden in staging/production")
