"""Tests for production deployment safety guards (H4, M11)."""
from __future__ import annotations

import os
from unittest.mock import patch

import pytest


def test_dev_token_rejected_in_production_env():
    """H4: dev-token must be rejected when APP_ENV=production."""
    from services.api.fastapi_app import _register_env_dev_token
    from packages.auth import AuthTokenService

    svc = AuthTokenService()
    with (
        patch.dict(os.environ, {"APP_ENV": "production", "BUILDER_API_TOKEN": "dev-token", "BUILDER_DEV_USER_ID": "u", "BUILDER_DEV_PROJECT_ID": "p", "BUILDER_DEV_ROLE": "builder"}),
        pytest.raises(ValueError, match="dev-token.*production"),
    ):
        _register_env_dev_token(svc)


def test_custom_token_accepted_in_production_env():
    """H4: custom tokens must work in production."""
    from services.api.fastapi_app import _register_env_dev_token
    from packages.auth import AuthTokenService

    svc = AuthTokenService()
    with patch.dict(os.environ, {"APP_ENV": "production", "BUILDER_API_TOKEN": "my-secret-prod-key-2026", "BUILDER_DEV_USER_ID": "u", "BUILDER_DEV_PROJECT_ID": "p", "BUILDER_DEV_ROLE": "builder"}):
        _register_env_dev_token(svc)
    ctx = svc.verify_token("my-secret-prod-key-2026")
    assert ctx.user_id == "u"


def test_dev_token_accepted_in_dev_env():
    """H4: dev-token must be accepted in non-production environments."""
    from services.api.fastapi_app import _register_env_dev_token
    from packages.auth import AuthTokenService

    svc = AuthTokenService()
    with patch.dict(os.environ, {"BUILDER_API_TOKEN": "dev-token", "BUILDER_DEV_USER_ID": "u", "BUILDER_DEV_PROJECT_ID": "p", "BUILDER_DEV_ROLE": "builder"}):
        _register_env_dev_token(svc)
    ctx = svc.verify_token("dev-token")
    assert ctx.user_id == "u"


def test_docker_compose_postgres_password_uses_env_var():
    """M11: docker-compose must use env var for postgres password."""
    import re

    content = open("docker-compose.yml").read()
    # Check that POSTGRES_PASSWORD uses variable substitution
    pattern = r"POSTGRES_PASSWORD:\s*\$\{[^}]+\}"
    assert re.search(pattern, content), (
        "POSTGRES_PASSWORD in docker-compose.yml should use ${POSTGRES_PASSWORD:-...} "
        "variable substitution, not a hardcoded value"
    )


def test_docker_compose_postgres_localhost_binding():
    """M10: Postgres port should bind to localhost only."""
    import re

    content = open("docker-compose.yml").read()
    # Check postgres port binding is localhost-only
    lines = content.split("\n")
    in_postgres = False
    for i, line in enumerate(lines):
        if "postgres:" in line and "image:" not in line and "container_name:" not in line:
            in_postgres = True
        if in_postgres and "5432:5432" in line:
            assert "127.0.0.1" in line, (
                "Postgres port should bind to 127.0.0.1:5432:5432 for local-only access"
            )
            break
