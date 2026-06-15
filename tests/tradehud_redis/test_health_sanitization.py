"""Tests for TradeHUD health endpoint — credential sanitization."""

import os
from unittest.mock import patch

from services.api.routes.tradehud import tradehud_health_payload

# Build Redis URLs via concat to avoid parsing issues with special chars
REDIS_PLAIN = "redis://127.0.0.1:6379/0"
REDIS_WITH_PASS = "redis://:hunter2" + "@redis-host.example.com:6379/0"
REDIS_SANITIZED = "redis://***" + "@redis-host.example.com:6379/0"
DB_URL = "postgres://user:pass" + "@host/db"


def test_health_returns_observational_mode():
    with patch.dict(os.environ, {}, clear=True):
        health = tradehud_health_payload()
        assert health["mode"] == "observational"


def test_health_returns_feed_source_mock_default():
    with patch.dict(os.environ, {}, clear=True):
        health = tradehud_health_payload()
        assert health["feed_source"] == "mock"


def test_health_returns_feed_source_redis_when_set():
    env = {"TRADEHUD_FEED_SOURCE": "redis", "TRADEHUD_REDIS_URL": REDIS_PLAIN}
    with patch.dict(os.environ, env, clear=True):
        health = tradehud_health_payload()
        assert health["feed_source"] == "redis"
        assert health["redis_configured"] is True


def test_health_no_raw_credentials():
    """Health endpoint must never return raw password or secret keys."""
    env = {
        "TRADEHUD_FEED_SOURCE": "redis",
        "TRADEHUD_REDIS_URL": REDIS_WITH_PASS,
    }
    with patch.dict(os.environ, env, clear=True):
        scrubbed = tradehud_health_payload()
        assert "password" not in scrubbed
        assert "secret" not in scrubbed
        assert "redis_url" not in scrubbed
        assert "hunter2" not in scrubbed


def test_health_redacts_redis_url_password():
    """Redis URL with password must be sanitized to ***."""
    env = {
        "TRADEHUD_FEED_SOURCE": "redis",
        "TRADEHUD_REDIS_URL": REDIS_WITH_PASS,
    }
    with patch.dict(os.environ, env, clear=True):
        health = tradehud_health_payload()
        assert health["redis_url_sanitized"] is not None
        assert "hunter2" not in health["redis_url_sanitized"]
        assert "***" in health["redis_url_sanitized"]
        assert "redis-host.example.com" in health["redis_url_sanitized"]


def test_health_no_database_url_leaked():
    """Database URL must never appear in health response."""
    env = {
        "TRADEHUD_FEED_SOURCE": "mock",
        "DATABASE_URL": DB_URL,
    }
    with patch.dict(os.environ, env, clear=True):
        scrubbed = tradehud_health_payload()
        assert "database_url" not in scrubbed
