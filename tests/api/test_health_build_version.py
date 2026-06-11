"""API /health/build version tests — Segment 1."""
import os

import pytest


def test_health_build_includes_version_and_git_fields() -> None:
    from services.api.fastapi_app import create_fastapi_app

    app = create_fastapi_app(artifact_store=None, rate_limiter=None)
    client = pytest.importorskip("fastapi.testclient").TestClient(app)
    resp = client.get("/health/build")
    body = resp.json()
    assert "version" in body
    assert "git_commit" in body
    assert "build_time_utc" in body
    assert "schema_version" in body
    assert "source" in body


def test_health_build_commit_reflects_env() -> None:
    from services.api.fastapi_app import create_fastapi_app

    os.environ["BUILDER_GIT_COMMIT"] = "abc123def"
    try:
        app = create_fastapi_app(artifact_store=None, rate_limiter=None)
        client = pytest.importorskip("fastapi.testclient").TestClient(app)
        resp = client.get("/health/build")
        assert resp.json()["git_commit"] == "abc123def"
    finally:
        os.environ.pop("BUILDER_GIT_COMMIT", None)


def test_health_build_branch_reflects_env() -> None:
    from services.api.fastapi_app import create_fastapi_app

    os.environ["BUILDER_GIT_BRANCH"] = "feat/test-branch"
    try:
        app = create_fastapi_app(artifact_store=None, rate_limiter=None)
        client = pytest.importorskip("fastapi.testclient").TestClient(app)
        resp = client.get("/health/build")
        assert resp.json()["git_branch"] == "feat/test-branch"
    finally:
        os.environ.pop("BUILDER_GIT_BRANCH", None)
