"""Tests for BuilderProductionConfig — Segment D v4.

Verifies production startup fails without required config.
"""
from __future__ import annotations

import os
from unittest.mock import patch

import pytest


class TestBuilderProductionConfig:
    """Verify production config validation."""

    def _make_config(self, **overrides):
        from packages.config.production import BuilderProductionConfig
        defaults = dict(
            builder_env="production",
            api_token="a" * 32,
            database_url="postgresql://builder:pass@localhost/builder",
            redis_url="redis://localhost:6379",
            artifact_backend="s3",
            s3_bucket="builder-artifacts",
            s3_endpoint_url="http://localhost:9000",
            s3_access_key="minioadmin",
            s3_secret_key="minioadmin",
            cors_origins='["https://builder.example.com"]',
        )
        defaults.update(overrides)
        return BuilderProductionConfig(**defaults)

    def test_valid_production_config_passes(self):
        config = self._make_config()
        assert config.builder_env == "production"

    def test_missing_api_token_fails(self):
        from packages.config.production import BuilderProductionConfig
        with pytest.raises(ValueError, match="api_token"):
            self._make_config(api_token="")

    def test_short_api_token_fails(self):
        from packages.config.production import BuilderProductionConfig
        with pytest.raises(ValueError, match="api_token"):
            self._make_config(api_token="short")

    def test_demo_token_rejected_in_production(self):
        from packages.config.production import BuilderProductionConfig
        with pytest.raises(ValueError, match="demo|dev"):
            self._make_config(api_token="demo-token-for-testing-only")

    def test_missing_database_url_fails(self):
        from packages.config.production import BuilderProductionConfig
        with pytest.raises(ValueError, match="database"):
            self._make_config(database_url="")

    def test_missing_redis_url_fails(self):
        from packages.config.production import BuilderProductionConfig
        with pytest.raises(ValueError, match="redis"):
            self._make_config(redis_url="")

    def test_local_artifact_backend_rejected(self):
        from packages.config.production import BuilderProductionConfig
        with pytest.raises(ValueError, match="artifact"):
            self._make_config(artifact_backend="local")

    def test_wildcard_cors_rejected(self):
        from packages.config.production import BuilderProductionConfig
        with pytest.raises(Exception, match="cors"):
            self._make_config(cors_origins='["*"]')

    def test_browser_token_flag_rejected(self):
        from packages.config.production import BuilderProductionConfig
        with pytest.raises(ValueError, match="NEXT_PUBLIC"):
            self._make_config(has_browser_api_token=True)

    def test_missing_s3_bucket_fails_with_s3_backend(self):
        from packages.config.production import BuilderProductionConfig
        with pytest.raises(ValueError, match="s3"):
            self._make_config(s3_bucket="")

    def test_validate_from_env_success(self):
        from packages.config.production import validate_production_config_from_env
        env = {
            "BUILDER_ENV": "production",
            "BUILDER_API_TOKEN": "a" * 32,
            "BUILDER_DATABASE_URL": "postgresql://builder:pass@localhost/builder",
            "BUILDER_REDIS_URL": "redis://localhost:6379",
            "BUILDER_ARTIFACT_BACKEND": "s3",
            "BUILDER_S3_BUCKET": "builder-artifacts",
            "BUILDER_S3_ENDPOINT_URL": "http://localhost:9000",
            "BUILDER_S3_ACCESS_KEY": "minioadmin",
            "BUILDER_S3_SECRET_KEY": "minioadmin",
            "BUILDER_CORS_ORIGINS": '["https://builder.example.com"]',
        }
        with patch.dict(os.environ, env, clear=True):
            config = validate_production_config_from_env()
            assert config.builder_env == "production"

    def test_validate_from_env_failure(self):
        from packages.config.production import validate_production_config_from_env
        env = {"BUILDER_ENV": "production"}
        with patch.dict(os.environ, env, clear=True):
            with pytest.raises(ValueError):
                validate_production_config_from_env()
