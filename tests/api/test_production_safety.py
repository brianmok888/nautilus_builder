"""Tests for production deployment safety guards (H4, M11)."""
from __future__ import annotations

import os
import sys
import types
from unittest.mock import patch

import pytest


def _install_fake_fastapi(monkeypatch) -> None:
    from tests.api.test_fastapi_app import _FakeFastAPI, _FakeJSONResponse

    fake_fastapi_module = types.SimpleNamespace(FastAPI=_FakeFastAPI, Header=lambda default=None: default)
    monkeypatch.setitem(sys.modules, "fastapi", fake_fastapi_module)
    monkeypatch.setitem(sys.modules, "fastapi.responses", types.SimpleNamespace(JSONResponse=_FakeJSONResponse))


def _clear_policy_env(monkeypatch) -> None:
    for key in (
        "APP_ENV",
        "BUILDER_ENV",
        "BUILDER_API_TOKEN",
        "BUILDER_DEV_AUTH_TOKEN",
        "BUILDER_DEV_USER_ID",
        "BUILDER_DEV_PROJECT_ID",
        "BUILDER_DEV_ROLE",
        "NEXT_PUBLIC_BUILDER_API_TOKEN",
        "BUILDER_CORS_ORIGINS",
        "BUILDER_AI_AUDIT_SQLITE_PATH",
        "BUILDER_RATE_LIMIT_BACKEND",
        "BUILDER_REDIS_URL",
    ):
        monkeypatch.delenv(key, raising=False)


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
    with patch.dict(os.environ, {"APP_ENV": "production", "BUILDER_API_TOKEN": "prod-token-1234567890-1234567890", "BUILDER_DEV_USER_ID": "u", "BUILDER_DEV_PROJECT_ID": "p", "BUILDER_DEV_ROLE": "builder"}):
        _register_env_dev_token(svc)
    ctx = svc.verify_token("prod-token-1234567890-1234567890")
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

def test_fastapi_startup_rejects_short_production_token(monkeypatch, tmp_path) -> None:
    _install_fake_fastapi(monkeypatch)
    _clear_policy_env(monkeypatch)
    monkeypatch.setenv("BUILDER_ENV", "production")
    monkeypatch.setenv("BUILDER_API_TOKEN", "short-production-token")
    monkeypatch.setenv("BUILDER_CORS_ORIGINS", "https://builder.example.com")
    monkeypatch.setenv("BUILDER_AI_AUDIT_SQLITE_PATH", str(tmp_path / "audit.sqlite"))

    from services.api.fastapi_app import create_fastapi_app

    with pytest.raises(ValueError, match="BUILDER_API_TOKEN is too short"):
        create_fastapi_app()


def test_fastapi_startup_rejects_public_production_token(monkeypatch, tmp_path) -> None:
    _install_fake_fastapi(monkeypatch)
    _clear_policy_env(monkeypatch)
    monkeypatch.setenv("BUILDER_ENV", "production")
    monkeypatch.setenv("BUILDER_API_TOKEN", "prod-token-1234567890-1234567890")
    monkeypatch.setenv("NEXT_PUBLIC_BUILDER_API_TOKEN", "browser-visible-token")
    monkeypatch.setenv("BUILDER_CORS_ORIGINS", "https://builder.example.com")
    monkeypatch.setenv("BUILDER_AI_AUDIT_SQLITE_PATH", str(tmp_path / "audit.sqlite"))

    from services.api.fastapi_app import create_fastapi_app

    with pytest.raises(ValueError, match="NEXT_PUBLIC_BUILDER_API_TOKEN is forbidden"):
        create_fastapi_app()


def test_fastapi_startup_rejects_wildcard_production_cors(monkeypatch, tmp_path) -> None:
    _install_fake_fastapi(monkeypatch)
    _clear_policy_env(monkeypatch)
    monkeypatch.setenv("BUILDER_ENV", "production")
    monkeypatch.setenv("BUILDER_API_TOKEN", "prod-token-1234567890-1234567890")
    monkeypatch.setenv("BUILDER_CORS_ORIGINS", "*")
    monkeypatch.setenv("BUILDER_AI_AUDIT_SQLITE_PATH", str(tmp_path / "audit.sqlite"))

    from services.api.fastapi_app import create_fastapi_app

    with pytest.raises(ValueError, match="Wildcard CORS"):
        create_fastapi_app()


def test_fastapi_startup_treats_app_env_production_as_strictest_policy(monkeypatch, tmp_path) -> None:
    _install_fake_fastapi(monkeypatch)
    _clear_policy_env(monkeypatch)
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("BUILDER_ENV", "local")
    monkeypatch.setenv("BUILDER_API_TOKEN", "short-production-token")
    monkeypatch.setenv("BUILDER_CORS_ORIGINS", "*")
    monkeypatch.setenv("BUILDER_AI_AUDIT_SQLITE_PATH", str(tmp_path / "audit.sqlite"))

    from services.api.fastapi_app import create_fastapi_app

    with pytest.raises(ValueError, match="BUILDER_API_TOKEN is too short"):
        create_fastapi_app()


def test_fastapi_startup_rejects_dev_auth_token_with_conflicting_production_env(monkeypatch, tmp_path) -> None:
    _install_fake_fastapi(monkeypatch)
    _clear_policy_env(monkeypatch)
    monkeypatch.setenv("APP_ENV", "local")
    monkeypatch.setenv("BUILDER_ENV", "production")
    monkeypatch.setenv("BUILDER_API_TOKEN", "prod-token-1234567890-1234567890")
    monkeypatch.setenv("BUILDER_DEV_AUTH_TOKEN", "dev-token")
    monkeypatch.setenv("BUILDER_DEV_USER_ID", "u")
    monkeypatch.setenv("BUILDER_DEV_PROJECT_ID", "p")
    monkeypatch.setenv("BUILDER_CORS_ORIGINS", "https://builder.example.com")
    monkeypatch.setenv("BUILDER_AI_AUDIT_SQLITE_PATH", str(tmp_path / "audit.sqlite"))
    monkeypatch.setenv("BUILDER_RATE_LIMIT_BACKEND", "redis")
    monkeypatch.setenv("BUILDER_REDIS_URL", "redis://redis:6379/0")

    from services.api.fastapi_app import create_fastapi_app

    with pytest.raises(ValueError, match="dev-token.*production"):
        create_fastapi_app()


def test_fastapi_startup_treats_app_env_production_as_strictest_audit_store_policy(monkeypatch) -> None:
    """Production mode with APP_ENV=production requires both DB and audit store."""
    _install_fake_fastapi(monkeypatch)
    _clear_policy_env(monkeypatch)
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("BUILDER_ENV", "local")
    monkeypatch.setenv("BUILDER_API_TOKEN", "prod-token-1234567890-1234567890")
    monkeypatch.setenv("BUILDER_CORS_ORIGINS", "https://builder.example.com")
    monkeypatch.setenv("BUILDER_RATE_LIMIT_BACKEND", "redis")
    monkeypatch.setenv("BUILDER_REDIS_URL", "redis://redis:6379/0")
    monkeypatch.setenv("BUILDER_DATABASE_URL", "postgresql://test:test@localhost:5432/builder_test")
    monkeypatch.delenv("BUILDER_AI_AUDIT_SQLITE_PATH", raising=False)

    # Mock postgres since psycopg is not available in test env
    import packages.postgres as postgres

    class _FakeConn:
        """Fake Postgres connection for tests without psycopg."""
        def execute(self, *a, **kw):
            return self
        def fetchone(self):
            return None
        def fetchall(self):
            return []
        @property
        def rowcount(self):
            return 0
    _fake = _FakeConn()
    monkeypatch.setattr(postgres, "connect_pool", lambda dsn: _fake)
    monkeypatch.setattr(postgres, "apply_migrations", lambda conn: None)
    monkeypatch.setattr(postgres, "seed_default_market_data", lambda conn: None)

    from services.api.fastapi_app import create_fastapi_app

    with pytest.raises(ValueError, match="durable AI audit store is required"):
        create_fastapi_app()


def test_fastapi_startup_rejects_missing_production_rate_limit_backend(monkeypatch, tmp_path) -> None:
    _install_fake_fastapi(monkeypatch)
    _clear_policy_env(monkeypatch)
    monkeypatch.setenv("BUILDER_ENV", "production")
    monkeypatch.setenv("BUILDER_API_TOKEN", "prod-token-1234567890-1234567890")
    monkeypatch.setenv("BUILDER_CORS_ORIGINS", "https://builder.example.com")
    monkeypatch.setenv("BUILDER_AI_AUDIT_SQLITE_PATH", str(tmp_path / "audit.sqlite"))

    from services.api.fastapi_app import create_fastapi_app

    with pytest.raises(ValueError, match="BUILDER_RATE_LIMIT_BACKEND=redis"):
        create_fastapi_app()


def test_fastapi_startup_rejects_memory_production_rate_limit_backend(monkeypatch, tmp_path) -> None:
    _install_fake_fastapi(monkeypatch)
    _clear_policy_env(monkeypatch)
    monkeypatch.setenv("BUILDER_ENV", "production")
    monkeypatch.setenv("BUILDER_API_TOKEN", "prod-token-1234567890-1234567890")
    monkeypatch.setenv("BUILDER_CORS_ORIGINS", "https://builder.example.com")
    monkeypatch.setenv("BUILDER_AI_AUDIT_SQLITE_PATH", str(tmp_path / "audit.sqlite"))
    monkeypatch.setenv("BUILDER_RATE_LIMIT_BACKEND", "memory")

    from services.api.fastapi_app import create_fastapi_app

    with pytest.raises(ValueError, match="memory"):
        create_fastapi_app()


def test_fastapi_startup_rejects_redis_rate_limit_without_url(monkeypatch, tmp_path) -> None:
    _install_fake_fastapi(monkeypatch)
    _clear_policy_env(monkeypatch)
    monkeypatch.setenv("BUILDER_ENV", "production")
    monkeypatch.setenv("BUILDER_API_TOKEN", "prod-token-1234567890-1234567890")
    monkeypatch.setenv("BUILDER_CORS_ORIGINS", "https://builder.example.com")
    monkeypatch.setenv("BUILDER_AI_AUDIT_SQLITE_PATH", str(tmp_path / "audit.sqlite"))
    monkeypatch.setenv("BUILDER_RATE_LIMIT_BACKEND", "redis")

    from services.api.fastapi_app import create_fastapi_app

    with pytest.raises(ValueError, match="BUILDER_REDIS_URL"):
        create_fastapi_app()


def test_fastapi_startup_treats_app_env_production_as_strictest_rate_limit_policy(monkeypatch, tmp_path) -> None:
    _install_fake_fastapi(monkeypatch)
    _clear_policy_env(monkeypatch)
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("BUILDER_ENV", "local")
    monkeypatch.setenv("BUILDER_API_TOKEN", "prod-token-1234567890-1234567890")
    monkeypatch.setenv("BUILDER_CORS_ORIGINS", "https://builder.example.com")
    monkeypatch.setenv("BUILDER_AI_AUDIT_SQLITE_PATH", str(tmp_path / "audit.sqlite"))

    from services.api.fastapi_app import create_fastapi_app

    with pytest.raises(ValueError, match="BUILDER_RATE_LIMIT_BACKEND=redis"):
        create_fastapi_app()


def test_fastapi_startup_accepts_strong_production_policy(monkeypatch, tmp_path) -> None:
    _install_fake_fastapi(monkeypatch)
    _clear_policy_env(monkeypatch)
    monkeypatch.setenv("BUILDER_ENV", "production")
    monkeypatch.setenv("BUILDER_API_TOKEN", "prod-token-1234567890-1234567890")
    monkeypatch.setenv("BUILDER_CORS_ORIGINS", "https://builder.example.com")
    monkeypatch.setenv("BUILDER_AI_AUDIT_SQLITE_PATH", str(tmp_path / "audit.sqlite"))
    monkeypatch.setenv("BUILDER_RATE_LIMIT_BACKEND", "redis")
    monkeypatch.setenv("BUILDER_REDIS_URL", "redis://redis:6379/0")
    monkeypatch.setenv("BUILDER_DATABASE_URL", "postgresql://test:test@localhost:5432/builder_test")

    # Mock postgres since psycopg is not available in test env
    import packages.postgres as postgres

    class _FakeConn:
        """Fake Postgres connection for tests without psycopg."""
        def execute(self, *a, **kw):
            return self
        def fetchone(self):
            return None
        def fetchall(self):
            return []
        @property
        def rowcount(self):
            return 0
    _fake = _FakeConn()
    monkeypatch.setattr(postgres, "connect_pool", lambda dsn: _fake)
    monkeypatch.setattr(postgres, "apply_migrations", lambda conn: None)
    monkeypatch.setattr(postgres, "seed_default_market_data", lambda conn: None)

    from services.api.fastapi_app import create_fastapi_app

    app = create_fastapi_app()

    assert app.title == "Nautilus Builder API"


def test_packaged_api_entrypoint_uses_authenticated_fastapi_cli() -> None:
    pyproject = open("pyproject.toml").read()

    assert 'nautilus-builder-api = "services.api.fastapi_cli:main"' in pyproject
    assert 'nautilus-builder-api = "services.api.dev_server:main"' not in pyproject


def test_dependency_free_dev_server_rejects_non_loopback_without_unsafe_flag() -> None:
    from services.api.dev_server import validate_dev_server_bind

    with pytest.raises(ValueError, match="non-loopback"):
        validate_dev_server_bind("0.0.0.0", unsafe_allow_non_loopback=False)


def test_dependency_free_dev_server_allows_loopback_and_explicit_unsafe_flag() -> None:
    from services.api.dev_server import validate_dev_server_bind

    validate_dev_server_bind("127.0.0.1", unsafe_allow_non_loopback=False)
    validate_dev_server_bind("localhost", unsafe_allow_non_loopback=False)
    validate_dev_server_bind("0.0.0.0", unsafe_allow_non_loopback=True)
