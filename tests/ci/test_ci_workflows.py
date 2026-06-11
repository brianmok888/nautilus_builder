"""Tests for CI workflow structure — Segment C v4.

Verifies CI workflow files exist and contain required jobs.
"""
from __future__ import annotations

import os
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
WORKFLOWS_DIR = REPO_ROOT / ".github" / "workflows"


class TestCIWorkflows:
    """Verify CI workflow completeness per v4 spec."""

    def test_ci_workflow_exists(self) -> None:
        assert (WORKFLOWS_DIR / "ci.yml").is_file(), "ci.yml must exist"

    def test_security_workflow_exists(self) -> None:
        assert (WORKFLOWS_DIR / "security.yml").is_file(), "security.yml must exist"

    def test_docker_workflow_exists(self) -> None:
        assert (WORKFLOWS_DIR / "docker.yml").is_file(), "docker.yml must exist"

    def test_ci_has_backend_job(self) -> None:
        text = (WORKFLOWS_DIR / "ci.yml").read_text()
        assert "backend" in text.lower(), "ci.yml must have backend job"

    def test_ci_has_safety_job(self) -> None:
        text = (WORKFLOWS_DIR / "ci.yml").read_text()
        assert "safety" in text.lower(), "ci.yml must have safety job"

    def test_ci_has_frontend_job(self) -> None:
        text = (WORKFLOWS_DIR / "ci.yml").read_text()
        assert "frontend" in text.lower(), "ci.yml must have frontend job"

    def test_ci_triggers_on_pr(self) -> None:
        text = (WORKFLOWS_DIR / "ci.yml").read_text()
        assert "pull_request" in text, "ci.yml must trigger on pull_request"

    def test_ci_triggers_on_master_push(self) -> None:
        text = (WORKFLOWS_DIR / "ci.yml").read_text()
        assert "master" in text or "main" in text, "ci.yml must trigger on master/main push"

    def test_security_workflow_runs_authority_scan(self) -> None:
        text = (WORKFLOWS_DIR / "security.yml").read_text()
        assert "forbidden_authority" in text or "check_forbidden" in text, (
            "security.yml must run forbidden authority scan"
        )

    def test_security_workflow_runs_secret_scan(self) -> None:
        text = (WORKFLOWS_DIR / "security.yml").read_text()
        assert "gitleaks" in text.lower() or "check_secrets" in text, (
            "security.yml must run secret scanning"
        )

    def test_docker_workflow_validates_production_compose(self) -> None:
        text = (WORKFLOWS_DIR / "docker.yml").read_text()
        assert "production" in text.lower(), "docker.yml must validate production compose"

    def test_docker_workflow_builds_api_image(self) -> None:
        text = (WORKFLOWS_DIR / "docker.yml").read_text()
        assert "Dockerfile.api" in text, "docker.yml must build API image"
