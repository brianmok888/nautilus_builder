"""Tests for zero-config docker compose experience (S18)."""
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
COMPOSE_FILE = REPO_ROOT / "docker-compose.yml"
DOCKERFILE_API = REPO_ROOT / "Dockerfile.api"
DOCKERFILE_WEB = REPO_ROOT / "apps/web" / "Dockerfile"


class TestDockerComposeConfig:
    """Verify docker-compose.yml is valid and has needed features."""

    def test_compose_file_exists(self):
        assert COMPOSE_FILE.is_file()

    def test_compose_valid_yaml(self):
        import yaml
        content = COMPOSE_FILE.read_text()
        data = yaml.safe_load(content)
        assert "services" in data
        assert "postgres" in data["services"]
        assert "api" in data["services"]
        assert "web" in data["services"]

    def test_postgres_has_healthcheck(self):
        import yaml
        data = yaml.safe_load(COMPOSE_FILE.read_text())
        pg = data["services"]["postgres"]
        assert "healthcheck" in pg

    def test_api_depends_on_postgres_healthy(self):
        import yaml
        data = yaml.safe_load(COMPOSE_FILE.read_text())
        api = data["services"]["api"]
        assert "depends_on" in api
        pg_dep = api["depends_on"]["postgres"]
        assert pg_dep.get("condition") == "service_healthy"

    def test_api_has_healthcheck(self):
        import yaml
        data = yaml.safe_load(COMPOSE_FILE.read_text())
        api = data["services"]["api"]
        assert "healthcheck" in api

    def test_postgres_port_bound_localhost(self):
        import yaml
        data = yaml.safe_load(COMPOSE_FILE.read_text())
        ports = data["services"]["postgres"]["ports"]
        for port_mapping in ports:
            assert port_mapping.startswith("127.0.0.1:"), f"Postgres port must bind to localhost: {port_mapping}"

    def test_api_seeds_demo_data(self):
        import yaml
        data = yaml.safe_load(COMPOSE_FILE.read_text())
        api = data["services"]["api"]
        env = api.get("environment", {})
        assert "BUILDER_SEED_DEMO_STRATEGIES" in env


class TestDockerfiles:
    """Verify Dockerfiles are production-ready."""

    def test_api_dockerfile_exists(self):
        assert DOCKERFILE_API.is_file()

    def test_api_dockerfile_does_not_create_or_copy_local_credential_env_file(self):
        content = DOCKERFILE_API.read_text()
        assert ".env.execution.local" not in content
        assert "COPY .env" not in content
        assert "touch .env" not in content

    def test_api_dockerfile_has_healthcheck(self):
        content = DOCKERFILE_API.read_text()
        assert "HEALTHCHECK" in content

    def test_web_dockerfile_exists(self):
        assert DOCKERFILE_WEB.is_file()


class TestEnvExampleDockerCompat:
    """Verify .env.example covers all docker-compose env vars."""

    def test_env_example_covers_compose_vars(self):
        import yaml
        compose_vars = set()
        data = yaml.safe_load(COMPOSE_FILE.read_text())
        for svc in data["services"].values():
            for key in svc.get("environment", {}):
                # Strip ${...} and :-default patterns
                compose_vars.add(key)

        env_content = (REPO_ROOT / ".env.example").read_text()
        for var in compose_vars:
            assert var in env_content, f".env.example must document {var}"
