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
