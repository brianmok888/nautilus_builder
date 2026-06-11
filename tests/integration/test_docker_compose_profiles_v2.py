"""Docker compose profile contract tests — Segment 12."""
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]


class TestDockerComposeProfiles:
    def test_dev_compose_file_exists(self) -> None:
        assert (REPO_ROOT / "docker-compose.dev.yml").exists()

    def test_staging_compose_file_exists(self) -> None:
        assert (REPO_ROOT / "docker-compose.staging.yml").exists()

    def test_production_compose_file_exists(self) -> None:
        assert (REPO_ROOT / "docker-compose.production.yml").exists()

    def test_dockerfile_api_exists(self) -> None:
        assert (REPO_ROOT / "Dockerfile.api").exists()

    def test_dev_compose_includes_postgres(self) -> None:
        content = (REPO_ROOT / "docker-compose.dev.yml").read_text()
        assert "postgres" in content.lower() or "POSTGRES" in content

    def test_production_compose_includes_redis(self) -> None:
        content = (REPO_ROOT / "docker-compose.production.yml").read_text()
        assert "redis" in content.lower()
