"""CI gate tests — Segment 2.

Verifies GitHub Actions workflow files exist and contain required jobs.
These are structural tests; actual CI execution validates runtime behavior.
"""
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
WORKFLOWS_DIR = REPO_ROOT / ".github" / "workflows"


class TestCIGates:
    def test_ci_workflow_file_exists(self) -> None:
        assert (WORKFLOWS_DIR / "ci.yml").exists(), ".github/workflows/ci.yml missing"

    def test_ci_workflow_has_backend_job(self) -> None:
        content = (WORKFLOWS_DIR / "ci.yml").read_text()
        assert "backend" in content, "ci.yml missing 'backend' job"

    def test_ci_workflow_has_safety_job(self) -> None:
        content = (WORKFLOWS_DIR / "ci.yml").read_text()
        assert "safety" in content, "ci.yml missing 'safety' job"

    def test_ci_workflow_has_frontend_job(self) -> None:
        content = (WORKFLOWS_DIR / "ci.yml").read_text()
        assert "frontend" in content, "ci.yml missing 'frontend' job"

    def test_ci_workflow_runs_pytest(self) -> None:
        content = (WORKFLOWS_DIR / "ci.yml").read_text()
        assert "pytest" in content, "ci.yml missing pytest invocation"

    def test_ci_workflow_runs_forbidden_authority_scan(self) -> None:
        content = (WORKFLOWS_DIR / "ci.yml").read_text()
        assert "check_forbidden_authority" in content, "ci.yml missing authority scan"

    def test_ci_workflow_runs_frontend_typecheck_and_build(self) -> None:
        content = (WORKFLOWS_DIR / "ci.yml").read_text()
        assert "typecheck" in content, "ci.yml missing frontend typecheck"
        assert "build" in content, "ci.yml missing frontend build"

    def test_ci_workflow_does_not_leak_secrets(self) -> None:
        content = (WORKFLOWS_DIR / "ci.yml").read_text()
        # Should not contain real tokens
        assert "BUILDER_API_TOKEN" not in content or "${{" in content.split("BUILDER_API_TOKEN")[0][-20:], (
            "ci.yml may contain hardcoded secrets"
        )
