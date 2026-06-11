"""API /health/build version tests — Segment 1."""
import pytest


def test_health_build_includes_commit_and_build_time() -> None:
    from services.api.fastapi_app import create_fastapi_app

    app = create_fastapi_app(artifact_store=None, rate_limiter=None)
    client = pytest.importorskip("fastapi.testclient").TestClient(app)
    resp = client.get("/health/build")
    body = resp.json()
    assert "version" in body
    assert "commit" in body
    assert "build_time" in body


def test_health_build_commit_reflects_env() -> None:
    import os

    from services.api.fastapi_app import create_fastapi_app

    os.environ["GIT_COMMIT_SHA"] = "abc123"
    try:
        app = create_fastapi_app(artifact_store=None, rate_limiter=None)
        client = pytest.importorskip("fastapi.testclient").TestClient(app)
        resp = client.get("/health/build")
        assert resp.json()["commit"] == "abc123"
    finally:
        del os.environ["GIT_COMMIT_SHA"]
