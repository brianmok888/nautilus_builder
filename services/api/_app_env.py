"""Builder API environment/config startup helpers.

Extracted from services/api/fastapi_app.py to separate pure environment/config
startup validation from the FastAPI app factory. Behavior is identical; this
module is the new home for the env resolution, CORS/token/rate-limit startup
validation, dev-token registration, and AI-audit-store defaulting helpers.

These helpers are re-exported by fastapi_app for backward compatibility.
"""

from __future__ import annotations

import os
import sqlite3
from packages.ai_builder.provider import (
    DraftAuditStoreProtocol,
    RecordedAiDraftStore,
    SqliteAiDraftAuditStore,
)
from packages.auth import AuthTokenService, UserProjectContext
from packages.auth.policy import (
    BuilderEnvironment,
    validate_builder_env,
    validate_cors_config,
    validate_production_token,
    validate_rate_limit_config,
)

_UNSAFE_DEV_TOKENS = ["dev-token", "test-token", "change-me"]


def _cors_origins_from_env() -> list[str]:
    return [
        origin.strip()
        for origin in os.environ.get("BUILDER_CORS_ORIGINS", "").split(",")
        if origin.strip()
    ]


def _validate_startup_policy() -> None:
    env = _strictest_configured_env()
    validate_production_token(
        token=os.environ.get("BUILDER_API_TOKEN"),
        public_token=os.environ.get("NEXT_PUBLIC_BUILDER_API_TOKEN"),
        env=env,
    )
    validate_cors_config(origins=_cors_origins_from_env(), env=env)
    validate_rate_limit_config(
        env=env,
        backend=os.environ.get("BUILDER_RATE_LIMIT_BACKEND"),
        redis_url=os.environ.get("BUILDER_REDIS_URL"),
    )


def _strictest_configured_env() -> BuilderEnvironment:
    configured = []
    for raw in (os.environ.get("BUILDER_ENV", ""), os.environ.get("APP_ENV", "")):
        configured.append(validate_builder_env(raw))
    if not configured:
        return BuilderEnvironment.LOCAL
    priority = {
        BuilderEnvironment.LOCAL: 0,
        BuilderEnvironment.STAGING: 1,
        BuilderEnvironment.PRODUCTION: 2,
    }
    return max(configured, key=lambda env: priority[env])


def _env_user_project_context() -> UserProjectContext:
    return UserProjectContext(
        user_id=os.environ.get("BUILDER_DEV_USER_ID", "local_user"),
        project_id=os.environ.get("BUILDER_DEV_PROJECT_ID", "local_project"),
        role=os.environ.get("BUILDER_DEV_ROLE", "builder"),
    )


def _register_env_dev_token(auth_token_service: AuthTokenService) -> None:
    dev_auth_token = os.environ.get("BUILDER_DEV_AUTH_TOKEN")
    token = (dev_auth_token or os.environ.get("BUILDER_API_TOKEN") or "").strip()
    if not token:
        return
    environment = _strictest_configured_env()
    if environment != BuilderEnvironment.LOCAL and dev_auth_token is not None:
        raise ValueError(
            f"Refusing BUILDER_DEV_AUTH_TOKEN '{token}' in {environment.value} environment. "
            "Use BUILDER_API_TOKEN for staging/production server-side auth."
        )
    if environment != BuilderEnvironment.LOCAL and token in _UNSAFE_DEV_TOKENS:
        raise ValueError(
            f"Refusing to register known dev token '{token}' in {environment.value} environment. "
            "Set BUILDER_API_TOKEN to a strong secret."
        )
    auth_token_service.register_token(
        token=token,
        user_id=os.environ.get("BUILDER_DEV_USER_ID", "local_user"),
        project_id=os.environ.get("BUILDER_DEV_PROJECT_ID", "local_project"),
        role=os.environ.get("BUILDER_DEV_ROLE", "builder"),
    )


def _default_ai_audit_store(ai_audit_store: DraftAuditStoreProtocol | None) -> DraftAuditStoreProtocol:
    if ai_audit_store is not None:
        return ai_audit_store
    sqlite_path = os.environ.get("BUILDER_AI_AUDIT_SQLITE_PATH", "").strip()
    if sqlite_path:
        return SqliteAiDraftAuditStore(connection=sqlite3.connect(sqlite_path))
    environment = _strictest_configured_env()
    if environment == BuilderEnvironment.PRODUCTION:
        raise ValueError("durable AI audit store is required in production")
    return RecordedAiDraftStore()
