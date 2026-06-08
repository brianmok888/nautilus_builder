from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_dockerfile_does_not_copy_local_env_files() -> None:
    content = (ROOT / "Dockerfile.api").read_text()

    assert ".env.execution.local" not in content
    assert ".env.local" not in content
    assert "COPY .env" not in content


def test_dockerignore_excludes_secret_and_local_state_files() -> None:
    dockerignore = ROOT / ".dockerignore"

    assert dockerignore.exists(), ".dockerignore is required to keep .env* out of build context"
    patterns = dockerignore.read_text().splitlines()
    required = {".env*", ".git", ".next", "node_modules", ".artifacts", "*.sqlite", "__pycache__"}
    assert required.issubset(set(patterns))
