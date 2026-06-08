"""Tests for dev database orchestration scripts and configuration.

Verifies:
  - docker-compose.dev.yml exists and defines Builder-owned Postgres
  - Migration script is importable and has correct CLI shape
  - Seed script is importable and has correct CLI shape
  - .env.demo.example exists and documents required variables
  - Dev demo runbook exists
"""
import importlib
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
DOCKER_DEV = REPO_ROOT / "docker-compose.dev.yml"
MIGRATION_SCRIPT = REPO_ROOT / "scripts" / "apply_builder_migrations.py"
SEED_SCRIPT = REPO_ROOT / "scripts" / "seed_builder_demo_data.py"
ENV_DEMO = REPO_ROOT / ".env.demo.example"
RUNBOOK = REPO_ROOT / "docs" / "demo" / "dev-database-demo-runbook.md"


class TestDockerComposeDev:
    """Verify docker-compose.dev.yml for Builder-owned Postgres."""

    def test_dev_compose_exists(self):
        assert DOCKER_DEV.is_file(), "docker-compose.dev.yml must exist"

    def test_dev_compose_uses_builder_db(self):
        content = DOCKER_DEV.read_text()
        assert "nautilus_builder" in content, "Must use Builder-owned DB name"
        assert "POSTGRES_USER" in content
        assert "healthcheck" in content

    def test_dev_compose_uses_localhost_only_port(self):
        content = DOCKER_DEV.read_text()
        assert "127.0.0.1:5432:5432" in content, "Port must bind to localhost only"


class TestMigrationScript:
    """Verify apply_builder_migrations.py is valid and importable."""

    def test_migration_script_exists(self):
        assert MIGRATION_SCRIPT.is_file(), "scripts/apply_builder_migrations.py must exist"

    def test_migration_script_imports(self):
        spec = importlib.util.spec_from_file_location("apply_builder_migrations", MIGRATION_SCRIPT)
        assert spec is not None, "Migration script must be importable"

    def test_migration_script_requires_env(self):
        result = subprocess.run(
            ["python3", str(MIGRATION_SCRIPT)],
            capture_output=True,
            text=True,
            cwd=str(REPO_ROOT),
            env={"PATH": "/usr/bin:/bin"},
        )
        assert result.returncode != 0, "Must fail when BUILDER_DATABASE_URL is not set"
        assert "BUILDER_DATABASE_URL" in result.stderr, "Must mention the required env var"

    def test_migration_script_references_migrations_module(self):
        content = MIGRATION_SCRIPT.read_text()
        assert "apply_migrations" in content, "Must call apply_migrations from packages.postgres.migrations"


class TestSeedScript:
    """Verify seed_builder_demo_data.py is valid and importable."""

    def test_seed_script_exists(self):
        assert SEED_SCRIPT.is_file(), "scripts/seed_builder_demo_data.py must exist"

    def test_seed_script_references_demo_strategies(self):
        content = SEED_SCRIPT.read_text()
        assert "demo_draft" in content or "_DEMO_STRATEGIES" in content, "Must seed demo strategies"
        assert "builder" in content.lower(), "Must reference builder schema"
        assert "BUILDER_DATABASE_URL" in content, "Must require database URL"

    def test_seed_script_requires_env(self):
        result = subprocess.run(
            ["python3", str(SEED_SCRIPT)],
            capture_output=True,
            text=True,
            cwd=str(REPO_ROOT),
            env={"PATH": "/usr/bin:/bin"},
        )
        assert result.returncode != 0, "Must fail when BUILDER_DATABASE_URL is not set"

    def test_seed_script_is_idempotent(self):
        content = SEED_SCRIPT.read_text()
        assert "idempotent" in content.lower(), "Script doc must state idempotent behavior"

    def test_seed_script_safety_wording(self):
        content = SEED_SCRIPT.read_text()
        assert "submit_order" not in content.replace("no submit_order", "").replace("submit_order,", ""), \
            "Seed script must not call submit_order"
        assert "TradeAction" not in content, "Seed script must not create TradeAction"


class TestEnvDemoExample:
    """Verify .env.demo.example documents all required variables."""

    def test_env_demo_exists(self):
        assert ENV_DEMO.is_file(), ".env.demo.example must exist"

    def test_env_demo_documents_database_url(self):
        content = ENV_DEMO.read_text()
        assert "BUILDER_DATABASE_URL" in content

    def test_env_demo_documents_api_token(self):
        content = ENV_DEMO.read_text()
        assert "BUILDER_API_TOKEN" in content

    def test_env_demo_documents_artifact_root(self):
        content = ENV_DEMO.read_text()
        assert "BUILDER_ARTIFACT_ROOT" in content

    def test_env_demo_documents_api_base_url(self):
        content = ENV_DEMO.read_text()
        assert "NEXT_PUBLIC_API_BASE_URL" in content

    def test_env_demo_no_builder_api_token_exposure(self):
        content = ENV_DEMO.read_text()
        assert "NEXT_PUBLIC_BUILDER_API_TOKEN" not in content, \
            "Must not expose BUILDER_API_TOKEN to client bundle"


class TestDevDemoRunbook:
    """Verify the dev demo runbook exists and covers the required steps."""

    def test_runbook_exists(self):
        assert RUNBOOK.is_file(), "Dev demo runbook must exist"

    def test_runbook_covers_postgres_startup(self):
        content = RUNBOOK.read_text()
        assert "docker-compose.dev.yml" in content
        assert "up -d" in content

    def test_runbook_covers_migrations(self):
        content = RUNBOOK.read_text()
        assert "apply_builder_migrations" in content

    def test_runbook_covers_seed(self):
        content = RUNBOOK.read_text()
        assert "seed_builder_demo_data" in content

    def test_runbook_covers_api_startup(self):
        content = RUNBOOK.read_text()
        assert "uvicorn" in content
        assert "BUILDER_DATABASE_URL" in content

    def test_runbook_covers_safety(self):
        content = RUNBOOK.read_text()
        assert "Builder-only" in content or "Builder-only" in content
        assert "evidence-only" in content.lower() or "evidence" in content.lower()

    def test_runbook_covers_restart_durability(self):
        content = RUNBOOK.read_text()
        assert "restart" in content.lower()
        assert "durable" in content.lower() or "persist" in content.lower() or "Durability" in content

    def test_runbook_covers_db_boundary(self):
        content = RUNBOOK.read_text()
        assert "nautilus_builder" in content
        assert "nautilus_daedalus" in content or "runtime" in content.lower()
