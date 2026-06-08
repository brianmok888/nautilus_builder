"""Tests for docker-compose profile validity and release posture."""
from __future__ import annotations

from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[2]


def _load_compose(path: Path) -> dict:
    return yaml.safe_load(path.read_text())


class TestLocalCompose:
    def test_postgres_present(self):
        compose = _load_compose(ROOT / "docker-compose.yml")
        assert "postgres" in compose["services"]

    def test_api_present(self):
        compose = _load_compose(ROOT / "docker-compose.yml")
        assert "api" in compose["services"]

    def test_web_present(self):
        compose = _load_compose(ROOT / "docker-compose.yml")
        assert "web" in compose["services"]

    def test_postgres_port_bound_localhost(self):
        compose = _load_compose(ROOT / "docker-compose.yml")
        ports = compose["services"]["postgres"]["ports"]
        assert any("127.0.0.1" in p for p in ports)

    def test_health_checks_present(self):
        compose = _load_compose(ROOT / "docker-compose.yml")
        for svc in ("postgres", "api"):
            assert "healthcheck" in compose["services"][svc], f"{svc} missing healthcheck"

    def test_web_proxy_uses_server_side_api_token(self):
        compose = _load_compose(ROOT / "docker-compose.yml")
        env = compose["services"]["web"]["environment"]
        assert env["BUILDER_API_TOKEN"] == "${BUILDER_API_TOKEN:?Set BUILDER_API_TOKEN in .env}"
        assert "NEXT_PUBLIC_BUILDER_API_TOKEN" not in env

    def test_web_port_bound_localhost_for_token_proxy(self):
        compose = _load_compose(ROOT / "docker-compose.yml")
        ports = compose["services"]["web"]["ports"]
        assert any("127.0.0.1:3000:3000" in port for port in ports)


class TestStagingCompose:
    def test_redis_present(self):
        compose = _load_compose(ROOT / "docker-compose.staging.yml")
        assert "redis" in compose["services"]

    def test_minio_present(self):
        compose = _load_compose(ROOT / "docker-compose.staging.yml")
        assert "minio" in compose["services"]

    def test_builder_env_is_staging(self):
        compose = _load_compose(ROOT / "docker-compose.staging.yml")
        env = compose["services"]["api"]["environment"]
        assert env["BUILDER_ENV"] == "staging"

    def test_rate_limit_backend_is_redis(self):
        compose = _load_compose(ROOT / "docker-compose.staging.yml")
        env = compose["services"]["api"]["environment"]
        assert env["BUILDER_RATE_LIMIT_BACKEND"] == "redis"

    def test_artifact_backend_is_s3(self):
        compose = _load_compose(ROOT / "docker-compose.staging.yml")
        env = compose["services"]["api"]["environment"]
        assert env["BUILDER_ARTIFACT_BACKEND"] == "s3"

    def test_web_proxy_does_not_receive_server_side_api_token(self):
        compose = _load_compose(ROOT / "docker-compose.staging.yml")
        env = compose["services"]["web"]["environment"]
        assert "BUILDER_API_TOKEN" not in env
        assert "NEXT_PUBLIC_BUILDER_API_TOKEN" not in env


class TestProductionCompose:
    def test_redis_present(self):
        compose = _load_compose(ROOT / "docker-compose.production.yml")
        assert "redis" in compose["services"]

    def test_minio_present(self):
        compose = _load_compose(ROOT / "docker-compose.production.yml")
        assert "minio" in compose["services"]

    def test_builder_env_is_production(self):
        compose = _load_compose(ROOT / "docker-compose.production.yml")
        env = compose["services"]["api"]["environment"]
        assert env["BUILDER_ENV"] == "production"

    def test_api_token_is_required_variable(self):
        compose = _load_compose(ROOT / "docker-compose.production.yml")
        env = compose["services"]["api"]["environment"]
        token = env.get("BUILDER_API_TOKEN", "")
        assert "${BUILDER_API_TOKEN" in token  # Uses variable substitution, not hardcoded

    def test_no_next_public_token(self):
        compose = _load_compose(ROOT / "docker-compose.production.yml")
        env = compose["services"]["api"]["environment"]
        for key in env:
            assert not key.startswith("NEXT_PUBLIC_"), f"NEXT_PUBLIC_ found in production: {key}"

    def test_web_proxy_does_not_receive_server_side_api_token(self):
        compose = _load_compose(ROOT / "docker-compose.production.yml")
        env = compose["services"]["web"]["environment"]
        assert "BUILDER_API_TOKEN" not in env
        assert "NEXT_PUBLIC_BUILDER_API_TOKEN" not in env

    def test_redis_password_required(self):
        compose = _load_compose(ROOT / "docker-compose.production.yml")
        redis_cmd = compose["services"]["redis"]["command"]
        assert "requirepass" in redis_cmd

    def test_restart_policies(self):
        compose = _load_compose(ROOT / "docker-compose.production.yml")
        for svc_name in ("postgres", "redis", "minio", "api", "web"):
            svc = compose["services"][svc_name]
            assert svc.get("restart") == "unless-stopped", f"{svc_name} missing restart policy"

    def test_all_services_depend_on_healthy(self):
        compose = _load_compose(ROOT / "docker-compose.production.yml")
        api = compose["services"]["api"]
        for dep_name, dep_config in api.get("depends_on", {}).items():
            assert dep_config.get("condition") == "service_healthy", f"api->{dep_name} not health-gated"


class TestReleasePosture:
    def test_release_md_exists(self):
        assert (ROOT / "RELEASE.md").exists()

    def test_changelog_exists(self):
        assert (ROOT / "CHANGELOG.md").exists()

    def test_deployment_guide_exists(self):
        assert (ROOT / "docs" / "deployment_guide.md").exists()

    def test_operations_guide_exists(self):
        assert (ROOT / "docs" / "operations.md").exists()

    def test_env_production_example_exists(self):
        assert (ROOT / ".env.production.example").exists()

    def test_staging_compose_exists(self):
        assert (ROOT / "docker-compose.staging.yml").exists()

    def test_production_compose_exists(self):
        assert (ROOT / "docker-compose.production.yml").exists()
