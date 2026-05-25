from __future__ import annotations

import tomllib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def test_python_project_declares_runtime_and_test_dependencies() -> None:
    pyproject = tomllib.loads((ROOT / "pyproject.toml").read_text())

    dependencies = set(pyproject["project"]["dependencies"])
    optional_test = set(pyproject["project"]["optional-dependencies"]["test"])

    assert any(dependency.startswith("fastapi") for dependency in dependencies)
    assert any(dependency.startswith("uvicorn") for dependency in dependencies)
    assert any(dependency.startswith("pydantic") for dependency in dependencies)
    assert any(dependency.startswith("pytest") for dependency in optional_test)


def test_ci_template_runs_python_contract_suite_pending_repository_activation() -> None:
    workflow = (ROOT / "infra" / "ci" / "github-actions-test.yml").read_text()

    assert "python -m pip install -e .[test]" in workflow
    assert "pytest tests/strategy_spec" in workflow
    assert "tests/workflow_spine" in workflow


def test_local_stack_defines_postgres_redis_and_object_storage_placeholders() -> None:
    compose = (ROOT / "infra" / "docker-compose.yml").read_text()

    assert "postgres:" in compose
    assert "redis:" in compose
    assert "object-storage:" in compose
    assert "POSTGRES_DB: nautilus_builder" in compose
    assert "redis-server" in compose


def test_ci_template_covers_runtime_replay_frontend_and_new_storage_suites() -> None:
    workflow = (ROOT / "infra" / "ci" / "github-actions-test.yml").read_text()

    assert "python -m compileall -q packages services tests" in workflow
    assert "tests/artifact_store" in workflow
    assert "tests/catalog_datasets" in workflow
    assert "check_nautilus_runtime_version" in workflow
    assert "npm run typecheck" in workflow
    assert "npm test" in workflow
    assert "npm run build" in workflow
    assert "npm run test:e2e" in workflow


def test_deployment_readiness_evidence_documents_remaining_authority_boundaries() -> None:
    evidence = (ROOT / "infra" / "deployment" / "production-readiness-evidence.md").read_text()

    assert "durable artifact storage" in evidence
    assert "user-selected catalog datasets" in evidence
    assert "StrategySpec-generated catalog replay" in evidence
    assert "authz/tenant controls" in evidence
    assert "no live order authority" in evidence
    assert "CI/deployment evidence" in evidence
