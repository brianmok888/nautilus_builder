"""Tests for v2 validation hardening — feature registry, authority rules, source health."""
from __future__ import annotations

import pytest

from packages.strategy_validation.authority_rules import check_authority
from packages.strategy_validation.feature_registry import (
    ALL_KNOWN_FEATURES,
    is_known_feature,
    is_microstructure_feature,
)
from packages.strategy_validation.reports import (
    ValidationIssue,
    ValidationReport,
    KNOWN_ERROR_CODES,
    KNOWN_WARNING_CODES,
)
from packages.strategy_validation.source_health import validate_source_health


class TestFeatureRegistry:
    def test_known_book_features(self):
        assert is_known_feature("book.best_bid")
        assert is_known_feature("book.spread_bps")

    def test_known_trade_features(self):
        assert is_known_feature("trades.delta")
        assert is_known_feature("trades.absorption_score")

    def test_known_vwap_features(self):
        assert is_known_feature("vwap.session")
        assert is_known_feature("vwap.session_distance_bps")

    def test_known_liquidation_features(self):
        assert is_known_feature("liquidation.cascade_risk")
        assert is_known_feature("liquidation.cluster_score")

    def test_known_funding_features(self):
        assert is_known_feature("funding.rate")
        assert is_known_feature("funding.zscore")

    def test_known_svp_features(self):
        assert is_known_feature("svp.poc")
        assert is_known_feature("svp.distance_to_poc_bps")

    def test_unknown_feature_rejected(self):
        assert not is_known_feature("nonexistent.feature_xyz")

    def test_classic_indicators_known(self):
        assert is_known_feature("ema")
        assert is_known_feature("rsi")

    def test_microstructure_detection(self):
        assert is_microstructure_feature("book.best_bid")
        assert is_microstructure_feature("trades.delta")
        assert not is_microstructure_feature("ema")
        assert not is_microstructure_feature("vwap.session")


class TestAuthorityRules:
    def test_signal_preview_only_passes(self):
        spec = {"output": {"mode": "signal_preview_only"}}
        assert check_authority(spec) == []

    def test_live_execution_mode_blocked(self):
        spec = {"output": {"mode": "live_execution"}}
        issues = check_authority(spec)
        assert "ERR_FORBIDDEN_OUTPUT_MODE" in issues

    def test_execution_authority_field_blocked(self):
        spec = {"output": {"mode": "signal_preview_only"}, "execution_authority": True}
        issues = check_authority(spec)
        assert "ERR_LIVE_AUTHORITY_FIELD" in issues

    def test_may_submit_order_blocked(self):
        spec = {"output": {"mode": "signal_preview_only"}, "may_submit_order": True}
        issues = check_authority(spec)
        assert "ERR_LIVE_AUTHORITY_FIELD" in issues

    def test_execution_authority_false_passes(self):
        spec = {"output": {"mode": "signal_preview_only"}, "execution_authority": False}
        assert check_authority(spec) == []


class TestSourceHealth:
    def test_missing_source_health_fails(self):
        spec = {"features": {"required": ["book.best_bid"]}}
        issues = validate_source_health(spec)
        assert "ERR_MISSING_SOURCE_HEALTH_REQUIREMENT" in issues

    def test_valid_source_health_passes(self):
        spec = {
            "features": {
                "required": ["book.best_bid"],
                "source_health": {"stale_policy": "block_signal", "book_age_ms_max": 500},
            }
        }
        issues = validate_source_health(spec)
        assert "ERR_MISSING_SOURCE_HEALTH_REQUIREMENT" not in issues

    def test_missing_stale_policy_warns(self):
        spec = {
            "features": {
                "required": ["book.best_bid"],
                "source_health": {"book_age_ms_max": 500},
            }
        }
        issues = validate_source_health(spec)
        assert "ERR_STALE_FEATURE_WITHOUT_POLICY" in issues


class TestValidationReport:
    def test_from_issues_empty_is_valid(self):
        report = ValidationReport.from_issues([])
        assert report.is_valid
        assert report.blocking_issue_count == 0

    def test_from_issues_with_blocking_error(self):
        issues = [
            ValidationIssue(
                severity="error",
                code="ERR_UNKNOWN_FEATURE_REF",
                message="Unknown feature: xyz",
                blocking=True,
            )
        ]
        report = ValidationReport.from_issues(issues)
        assert not report.is_valid
        assert report.blocking_issue_count == 1
        assert len(report.errors) == 1

    def test_from_issues_with_warning_still_valid(self):
        issues = [
            ValidationIssue(
                severity="warning",
                code="WARN_CLASSIC_INDICATOR_ONLY_STRATEGY",
                message="Only classic indicators",
                blocking=False,
            )
        ]
        report = ValidationReport.from_issues(issues)
        assert report.is_valid
        assert len(report.warnings) == 1

    def test_known_error_codes_are_comprehensive(self):
        # Verify all codes from spec are present
        expected = {
            "ERR_UNKNOWN_FEATURE_REF",
            "ERR_FORBIDDEN_OUTPUT_MODE",
            "ERR_LIVE_AUTHORITY_FIELD",
            "ERR_MISSING_SOURCE_HEALTH_REQUIREMENT",
            "ERR_RISK_LIMIT_MISSING",
            "ERR_REPLAY_DATASET_REQUIRED",
        }
        assert expected.issubset(KNOWN_ERROR_CODES)
