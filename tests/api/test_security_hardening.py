"""Tests for production security hardening: BUILDER_ENV, token validation, CORS, structured errors, request IDs."""
from __future__ import annotations

import os
import pytest

from packages.auth.policy import (
    validate_builder_env,
    validate_production_token,
    validate_cors_config,
    BuilderEnvironment,
)
from packages.errors.errors import (
    ErrorCode,
    StructuredError,
    error_response,
)


# --- BUILDER_ENV validation ---

class TestBuilderEnvValidation:
    def test_local_env_accepted(self):
        result = validate_builder_env("local")
        assert result == BuilderEnvironment.LOCAL

    def test_staging_env_accepted(self):
        result = validate_builder_env("staging")
        assert result == BuilderEnvironment.STAGING

    def test_production_env_accepted(self):
        result = validate_builder_env("production")
        assert result == BuilderEnvironment.PRODUCTION

    def test_empty_env_defaults_to_local(self):
        result = validate_builder_env("")
        assert result == BuilderEnvironment.LOCAL

    def test_unknown_env_raises(self):
        with pytest.raises(ValueError, match="unknown BUILDER_ENV"):
            validate_builder_env("unknown_env")


# --- Production token validation ---

class TestProductionTokenValidation:
    def test_local_accepts_any_token(self):
        # Should not raise
        validate_production_token(
            env=BuilderEnvironment.LOCAL,
            token="dev-token",
            public_token=None,
        )

    def test_production_rejects_missing_token(self):
        with pytest.raises(ValueError, match="BUILDER_API_TOKEN is required"):
            validate_production_token(
                env=BuilderEnvironment.PRODUCTION,
                token=None,
                public_token=None,
            )

    def test_production_rejects_dev_token(self):
        with pytest.raises(ValueError, match="forbidden in staging/production"):
            validate_production_token(
                env=BuilderEnvironment.PRODUCTION,
                token="dev-token",
                public_token=None,
            )

    def test_production_rejects_short_token(self):
        with pytest.raises(ValueError, match="too short"):
            validate_production_token(
                env=BuilderEnvironment.PRODUCTION,
                token="a" * 16,
                public_token=None,
            )

    def test_production_rejects_public_token(self):
        with pytest.raises(ValueError, match="NEXT_PUBLIC"):
            validate_production_token(
                env=BuilderEnvironment.PRODUCTION,
                token="a" * 32,
                public_token="some-public-token",
            )

    def test_production_accepts_strong_token(self):
        validate_production_token(
            env=BuilderEnvironment.PRODUCTION,
            token="a" * 32,
            public_token=None,
        )

    def test_staging_rejects_dev_token(self):
        with pytest.raises(ValueError, match="forbidden"):
            validate_production_token(
                env=BuilderEnvironment.STAGING,
                token="dev-token",
                public_token=None,
            )


# --- CORS validation ---

class TestCorsValidation:
    def test_local_allows_localhost(self):
        validate_cors_config(
            env=BuilderEnvironment.LOCAL,
            origins=["http://localhost:3000"],
        )

    def test_production_rejects_wildcard(self):
        with pytest.raises(ValueError, match="Wildcard CORS"):
            validate_cors_config(
                env=BuilderEnvironment.PRODUCTION,
                origins=["*"],
            )

    def test_production_rejects_empty_origins(self):
        with pytest.raises(ValueError, match="empty"):
            validate_cors_config(
                env=BuilderEnvironment.PRODUCTION,
                origins=[],
            )

    def test_production_accepts_explicit_origins(self):
        validate_cors_config(
            env=BuilderEnvironment.PRODUCTION,
            origins=["https://builder.example.com"],
        )

    def test_local_allows_empty_origins(self):
        validate_cors_config(
            env=BuilderEnvironment.LOCAL,
            origins=[],
        )


# --- Structured error codes ---

class TestStructuredErrors:
    def test_error_code_enum_exists(self):
        assert ErrorCode.AUTH_REQUIRED.value == "AUTH_REQUIRED"
        assert ErrorCode.AUTH_INVALID.value == "AUTH_INVALID"
        assert ErrorCode.VALIDATION_FAILED.value == "VALIDATION_FAILED"
        assert ErrorCode.RATE_LIMITED.value == "RATE_LIMITED"
        assert ErrorCode.PRODUCTION_CONFIG_INVALID.value == "PRODUCTION_CONFIG_INVALID"
        assert ErrorCode.PROMOTION_BLOCKED.value == "PROMOTION_BLOCKED"

    def test_error_response_structure(self):
        resp = error_response(
            code=ErrorCode.VALIDATION_FAILED,
            message="Strategy spec invalid",
            request_id="req-123",
        )
        assert resp["error"]["code"] == "VALIDATION_FAILED"
        assert resp["error"]["message"] == "Strategy spec invalid"
        assert resp["error"]["request_id"] == "req-123"

    def test_error_response_with_details(self):
        resp = error_response(
            code=ErrorCode.VALIDATION_FAILED,
            message="Validation failed",
            request_id="req-456",
            details=[{"path": "indicators[0].period", "message": "must be > 0"}],
        )
        assert len(resp["error"]["details"]) == 1
        assert resp["error"]["details"][0]["path"] == "indicators[0].period"
