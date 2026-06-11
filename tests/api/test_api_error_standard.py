"""Tests for API error standard and dependencies."""
from __future__ import annotations

from services.api.errors import ApiError
from services.api.dependencies import RateLimiterProtocol, ArtifactStoreProtocol


class TestApiError:
    def test_api_error_model(self):
        err = ApiError(
            error_code="not_found",
            message="Strategy not found",
            request_id="req_001",
            details={"strategy_id": "missing_001"},
        )
        assert err.error_code == "not_found"
        assert err.message == "Strategy not found"
        assert err.request_id == "req_001"
        assert err.details["strategy_id"] == "missing_001"

    def test_api_error_minimal(self):
        err = ApiError(error_code="validation_error", message="Invalid input")
        assert err.request_id is None
        assert err.details == {}

    def test_api_error_extra_fields_forbidden(self):
        import pytest
        with pytest.raises(Exception):
            ApiError(error_code="test", message="test", unknown="bad")

    def test_api_error_serializable(self):
        err = ApiError(error_code="test", message="test")
        d = err.model_dump()
        assert "error_code" in d
        assert "message" in d


class TestProtocols:
    def test_rate_limiter_protocol_exists(self):
        assert RateLimiterProtocol is not None

    def test_artifact_store_protocol_exists(self):
        assert ArtifactStoreProtocol is not None
