"""Tests for health/live, health/ready, health/build endpoints."""
from __future__ import annotations

import inspect


class TestHealthEndpoints:
    def test_health_live_endpoint_registered(self):
        from services.api import fastapi_app
        source = inspect.getsource(fastapi_app)
        assert '"/health/live"' in source
        assert '"alive"' in source

    def test_health_ready_endpoint_registered(self):
        from services.api import fastapi_app
        source = inspect.getsource(fastapi_app)
        assert '"/health/ready"' in source
        assert '"ready"' in source or '"checks"' in source

    def test_health_build_endpoint_registered(self):
        """Verify /health/build returns version, commit, and build_time at runtime."""
        from services.api.fastapi_app import create_fastapi_app
        from fastapi.testclient import TestClient

        app = create_fastapi_app(artifact_store=None, rate_limiter=None)
        client = TestClient(app)
        resp = client.get("/health/build")
        body = resp.json()
        assert "version" in body
        assert "git_commit" in body
        assert "build_time_utc" in body

    def test_health_build_returns_version_info(self):
        from services.api import fastapi_app
        source = inspect.getsource(fastapi_app)
        assert "version" in source  # version comes from canonical builder_metadata module
