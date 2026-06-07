"""Tests for StrategySpecMicrostructureV1: schema, features, source health, safety."""
from __future__ import annotations

import pytest
from pydantic import ValidationError

from packages.strategy_spec.microstructure import (
    FeatureSourceHealth,
    MicrostructureFeature,
    MicrostructureFeatureRef,
    MicrostructureRiskBlock,
    MicrostructureSignalRule,
    SourceHealth,
    StrategySpecClassicV1,
    StrategySpecMicrostructureV1,
)


# ---------------------------------------------------------------------------
# Feature enum coverage
# ---------------------------------------------------------------------------

class TestMicrostructureFeature:
    def test_all_features_defined(self):
        expected = [
            "obi", "spread_bps", "top_depth_usd", "depth_near_price_usd",
            "pull_stack_score", "cvd", "cvd_divergence", "absorption",
            "aggressive_buy_volume", "aggressive_sell_volume",
            "heatmap_liquidity", "liquidity_walls",
            "svp_poc", "svp_vah", "svp_val", "hvn", "lvn",
            "funding_rate", "funding_z_score",
            "liquidation_imbalance", "liquidation_clusters",
            "vwap_session", "anchored_vwap",
            "vpin_toxicity", "book_resilience", "liquidity_replenishment",
        ]
        for name in expected:
            assert MicrostructureFeature(name).value == name

    def test_total_feature_count(self):
        assert len(MicrostructureFeature) == 26


# ---------------------------------------------------------------------------
# Source health enum
# ---------------------------------------------------------------------------

class TestSourceHealth:
    def test_all_statuses_defined(self):
        assert SourceHealth.SOURCE_AVAILABLE.value == "source_available"
        assert SourceHealth.STALE.value == "stale"
        assert SourceHealth.MISSING.value == "missing"
        assert SourceHealth.TRUE_ZERO.value == "true_zero"
        assert SourceHealth.SYNTHETIC_FALLBACK_USED.value == "synthetic_fallback_used"


# ---------------------------------------------------------------------------
# FeatureSourceHealth
# ---------------------------------------------------------------------------

class TestFeatureSourceHealth:
    def test_healthy_source(self):
        h = FeatureSourceHealth(
            feature=MicrostructureFeature.OBI,
            source_available=True,
            last_update_ts_ns=1000,
            age_ms=50,
            source_status=SourceHealth.SOURCE_AVAILABLE,
        )
        assert h.source_available is True
        assert h.stale is False
        assert h.missing is False

    def test_stale_source(self):
        h = FeatureSourceHealth(
            feature=MicrostructureFeature.CVD,
            source_available=True,
            stale=True,
            age_ms=5000,
            source_status=SourceHealth.STALE,
        )
        assert h.stale is True

    def test_missing_source(self):
        h = FeatureSourceHealth(
            feature=MicrostructureFeature.VPIN_TOXICITY,
            source_available=False,
            missing=True,
            source_status=SourceHealth.MISSING,
        )
        assert h.missing is True

    def test_rejects_extra_fields(self):
        with pytest.raises(ValidationError):
            FeatureSourceHealth(
                feature=MicrostructureFeature.OBI,
                source_available=True,
                bogus=True,
            )


# ---------------------------------------------------------------------------
# MicrostructureFeatureRef
# ---------------------------------------------------------------------------

class TestMicrostructureFeatureRef:
    def test_required_feature(self):
        ref = MicrostructureFeatureRef(
            feature=MicrostructureFeature.OBI,
            required=True,
            max_staleness_ms=1000,
            fail_closed_on_missing=True,
        )
        assert ref.required is True
        assert ref.fail_closed_on_missing is True

    def test_optional_feature(self):
        ref = MicrostructureFeatureRef(
            feature=MicrostructureFeature.HEATMAP_LIQUIDITY,
            required=False,
            fail_closed_on_missing=False,
        )
        assert ref.required is False

    def test_rejects_negative_staleness(self):
        with pytest.raises(ValidationError):
            MicrostructureFeatureRef(
                feature=MicrostructureFeature.OBI,
                max_staleness_ms=-1,
            )

    def test_rejects_zero_staleness(self):
        with pytest.raises(ValidationError):
            MicrostructureFeatureRef(
                feature=MicrostructureFeature.OBI,
                max_staleness_ms=0,
            )


# ---------------------------------------------------------------------------
# MicrostructureSignalRule
# ---------------------------------------------------------------------------

class TestMicrostructureSignalRule:
    def test_valid_signal(self):
        rule = MicrostructureSignalRule(
            name="obi_long_entry",
            features=[
                MicrostructureFeatureRef(feature=MicrostructureFeature.OBI),
                MicrostructureFeatureRef(feature=MicrostructureFeature.CVD),
            ],
            condition="obi > 0.3 AND cvd > 0",
            direction="long",
            confidence_threshold=0.7,
        )
        assert rule.direction == "long"

    def test_rejects_empty_condition(self):
        with pytest.raises(ValidationError):
            MicrostructureSignalRule(
                name="bad",
                features=[MicrostructureFeatureRef(feature=MicrostructureFeature.OBI)],
                condition="   ",
            )

    def test_rejects_empty_features(self):
        with pytest.raises(ValidationError):
            MicrostructureSignalRule(
                name="bad",
                features=[],
                condition="obi > 0",
            )


# ---------------------------------------------------------------------------
# StrategySpecMicrostructureV1
# ---------------------------------------------------------------------------

def _make_spec(**overrides) -> StrategySpecMicrostructureV1:
    defaults = dict(
        version="1.0.0",
        adapter_id="binance",
        venue="BINANCE",
        instrument_id="BTCUSDT-PERP.BINANCE",
        features=[
            MicrostructureFeatureRef(
                feature=MicrostructureFeature.OBI,
                max_staleness_ms=5000,
            ),
            MicrostructureFeatureRef(
                feature=MicrostructureFeature.CVD,
                max_staleness_ms=3000,
            ),
            MicrostructureFeatureRef(
                feature=MicrostructureFeature.SPREAD_BPS,
                required=False,
            ),
        ],
        signals=[
            MicrostructureSignalRule(
                name="obi_long",
                features=[
                    MicrostructureFeatureRef(feature=MicrostructureFeature.OBI),
                ],
                condition="obi > 0.3",
                direction="long",
            ),
        ],
        risk=MicrostructureRiskBlock(
            max_position_notional_usd=10000.0,
            max_loss_notional_usd=500.0,
            max_hold_ms=3600000,
            min_signal_confidence=0.6,
        ),
    )
    defaults.update(overrides)
    return StrategySpecMicrostructureV1(**defaults)


class TestStrategySpecMicrostructureV1:
    def test_valid_spec(self):
        spec = _make_spec()
        assert spec.schema_version == "microstructure_v1"
        assert spec.output_mode == "signal_preview_only"
        assert spec.execution_authority is False

    def test_output_mode_locked(self):
        spec = _make_spec()
        assert spec.output_mode == "signal_preview_only"

    def test_execution_authority_locked_false(self):
        spec = _make_spec()
        assert spec.execution_authority is False

    def test_rejects_execution_authority_true(self):
        with pytest.raises(ValidationError):
            _make_spec(execution_authority=True)

    def test_rejects_wrong_schema_version(self):
        with pytest.raises(ValidationError):
            _make_spec(schema_version="classic_v1")

    def test_rejects_extra_fields(self):
        with pytest.raises(ValidationError):
            _make_spec(bogus=True)

    def test_get_required_features(self):
        spec = _make_spec()
        required = spec.get_required_features()
        assert len(required) == 2  # OBI + CVD (SPREAD_BPS is optional)
        assert all(f.required for f in required)

    def test_get_optional_features(self):
        spec = _make_spec()
        optional = spec.get_optional_features()
        assert len(optional) == 1  # SPREAD_BPS
        assert all(not f.required for f in optional)


# ---------------------------------------------------------------------------
# Source health validation
# ---------------------------------------------------------------------------

class TestSourceHealthValidation:
    def test_all_healthy_no_violations(self):
        spec = _make_spec()
        health = [
            FeatureSourceHealth(
                feature=MicrostructureFeature.OBI,
                source_available=True,
                source_status=SourceHealth.SOURCE_AVAILABLE,
            ),
            FeatureSourceHealth(
                feature=MicrostructureFeature.CVD,
                source_available=True,
                source_status=SourceHealth.SOURCE_AVAILABLE,
            ),
        ]
        violations = spec.validate_source_health(health)
        assert violations == []

    def test_missing_required_feature_violation(self):
        spec = _make_spec()
        health = [
            FeatureSourceHealth(
                feature=MicrostructureFeature.OBI,
                source_available=True,
                source_status=SourceHealth.SOURCE_AVAILABLE,
            ),
            # CVD is missing from health records
        ]
        violations = spec.validate_source_health(health)
        assert len(violations) == 1
        assert "cvd" in violations[0]

    def test_stale_feature_violation(self):
        spec = _make_spec()
        health = [
            FeatureSourceHealth(
                feature=MicrostructureFeature.OBI,
                source_available=True,
                stale=True,
                age_ms=10000,
                source_status=SourceHealth.STALE,
            ),
            FeatureSourceHealth(
                feature=MicrostructureFeature.CVD,
                source_available=True,
                source_status=SourceHealth.SOURCE_AVAILABLE,
            ),
        ]
        violations = spec.validate_source_health(health)
        assert len(violations) >= 1
        assert any("obi" in v and "stale" in v for v in violations)

    def test_synthetic_fallback_violation(self):
        spec = _make_spec()
        health = [
            FeatureSourceHealth(
                feature=MicrostructureFeature.OBI,
                source_available=True,
                synthetic_fallback_used=True,
                source_status=SourceHealth.SYNTHETIC_FALLBACK_USED,
            ),
            FeatureSourceHealth(
                feature=MicrostructureFeature.CVD,
                source_available=True,
                source_status=SourceHealth.SOURCE_AVAILABLE,
            ),
        ]
        violations = spec.validate_source_health(health)
        assert len(violations) >= 1
        assert any("synthetic" in v for v in violations)

    def test_optional_feature_missing_no_violation(self):
        spec = _make_spec()
        health = [
            FeatureSourceHealth(
                feature=MicrostructureFeature.OBI,
                source_available=True,
                source_status=SourceHealth.SOURCE_AVAILABLE,
            ),
            FeatureSourceHealth(
                feature=MicrostructureFeature.CVD,
                source_available=True,
                source_status=SourceHealth.SOURCE_AVAILABLE,
            ),
            # SPREAD_BPS (optional) is missing — should not be a violation
        ]
        violations = spec.validate_source_health(health)
        assert violations == []

    def test_missing_health_record_fail_closed(self):
        spec = _make_spec()
        violations = spec.validate_source_health([])  # no health records at all
        assert len(violations) == 2  # OBI + CVD both missing


# ---------------------------------------------------------------------------
# Backward compatibility: classic StrategySpec still works
# ---------------------------------------------------------------------------

class TestClassicSpecUnchanged:
    def test_import_works(self):
        assert StrategySpecClassicV1 is not None

    def test_classic_spec_not_microstructure(self):
        assert StrategySpecClassicV1 is not StrategySpecMicrostructureV1
