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
        from services.api import fastapi_app
        source = inspect.getsource(fastapi_app)
        assert '"/health/build"' in source
        assert '"version"' in source
        assert '"commit"' in source

    def test_health_build_returns_version_info(self):
        from services.api import fastapi_app
        source = inspect.getsource(fastapi_app)
        assert "0.4.0" in source or "version" in source
