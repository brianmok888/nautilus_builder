"""Tests for .env.example and operational scripts (S12)."""
import os
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
ENV_EXAMPLE = REPO_ROOT / ".env.example"
SCRIPTS_DIR = REPO_ROOT / "scripts"


class TestEnvExample:
    """Verify .env.example exists and documents all configurable env vars."""

    def test_env_example_exists(self):
        assert ENV_EXAMPLE.is_file(), ".env.example must exist at repo root"

    def test_env_example_documents_api_token(self):
        content = ENV_EXAMPLE.read_text()
        assert "BUILDER_API_TOKEN" in content, ".env.example must document BUILDER_API_TOKEN"

    def test_env_example_documents_database_url(self):
        content = ENV_EXAMPLE.read_text()
        assert "BUILDER_DATABASE_URL" in content or "POSTGRES_PASSWORD" in content, (
            ".env.example must document database connection"
        )

    def test_env_example_documents_cors(self):
        content = ENV_EXAMPLE.read_text()
        assert "BUILDER_CORS_ORIGINS" in content, ".env.example must document CORS setting"

    def test_env_example_has_no_real_secrets(self):
        content = ENV_EXAMPLE.read_text()
        # Should use placeholder values, not real ones
        for line in content.splitlines():
            line = line.strip()
            if "=" in line and not line.startswith("#"):
                key, _, value = line.partition("=")
                # Values should be placeholder-like
                assert len(value) < 80, f"Secret-looking value for {key} in .env.example"

    def test_env_example_documents_execution_local(self):
        content = ENV_EXAMPLE.read_text()
        assert ".env.execution.local" in content or "EXECUTION" in content.upper(), (
            ".env.example must mention .env.execution.local for venue credentials"
        )


class TestRunDevScript:
    """Verify scripts/run_dev.sh exists and is runnable."""

    def test_run_dev_sh_exists(self):
        script = SCRIPTS_DIR / "run_dev.sh"
        assert script.is_file(), "scripts/run_dev.sh must exist"

    def test_run_dev_sh_is_executable(self):
        script = SCRIPTS_DIR / "run_dev.sh"
        if script.is_file():
            assert os.access(script, os.X_OK), "scripts/run_dev.sh must be executable"

    def test_run_dev_sh_mentions_api(self):
        script = SCRIPTS_DIR / "run_dev.sh"
        if script.is_file():
            content = script.read_text()
            assert "uvicorn" in content or "api" in content.lower(), (
                "run_dev.sh should start the API server"
            )

    def test_run_dev_sh_has_help_flag(self):
        script = SCRIPTS_DIR / "run_dev.sh"
        if script.is_file():
            result = subprocess.run(
                ["bash", str(script), "--help"],
                capture_output=True,
                text=True,
                timeout=10,
                cwd=str(REPO_ROOT),
            )
            # Should exit cleanly (0 or show usage)
            assert result.returncode in (0, 1), f"run_dev.sh --help failed: {result.stderr}"


class TestRunTestsScript:
    """Verify scripts/run_tests.sh exists and is runnable."""

    def test_run_tests_sh_exists(self):
        script = SCRIPTS_DIR / "run_tests.sh"
        assert script.is_file(), "scripts/run_tests.sh must exist"

    def test_run_tests_sh_is_executable(self):
        script = SCRIPTS_DIR / "run_tests.sh"
        if script.is_file():
            assert os.access(script, os.X_OK), "scripts/run_tests.sh must be executable"

    def test_run_tests_sh_mentions_pytest(self):
        script = SCRIPTS_DIR / "run_tests.sh"
        if script.is_file():
            content = script.read_text()
            assert "pytest" in content, "run_tests.sh should run pytest"
