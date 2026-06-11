"""StrategySpec v2 model tests — Segment 4.

Tests that the v2 models can represent ND-style microstructure strategies
with full feature coverage, condition DSL, event detectors, archetypes,
risk contracts, and evidence requirements.
"""
import pytest

from packages.strategy_spec.models_v2 import (
    Archetype,
    ConditionDSL,
    ConditionPrimitive,
    EventDetector,
    EvidenceRequirement,
    FeatureGroup,
    FeatureInput,
    MarketType,
    Overlay,
    RiskContractV2,
    SourceHealthRequirement,
    StrategySpecV2,
    StrategySpecV2Metadata,
    StrategySpecV2Universe,
    SchemaVersion,
)


class TestStrategySpecV2Metadata:
    def test_metadata_fields(self) -> None:
        m = StrategySpecV2Metadata(
            strategy_id="strat_001",
            lineage_id="lineage_001",
            name="Test Strategy",
            version="1.0.0",
            schema_version=SchemaVersion.V2,
            created_by="user",
        )
        assert m.strategy_id == "strat_001"
        assert m.schema_version == "v2"

    def test_metadata_requires_strategy_id(self) -> None:
        with pytest.raises(Exception):
            StrategySpecV2Metadata(
                lineage_id="lineage_001",
                name="Test",
                version="1.0.0",
                schema_version=SchemaVersion.V2,
                created_by="user",
            )


class TestStrategySpecV2Universe:
    def test_universe_fields(self) -> None:
        u = StrategySpecV2Universe(
            venue="BINANCE",
            instrument_id="BTCUSDT-PERP.BINANCE",
            timeframe="1-MINUTE",
        )
        assert u.venue == "BINANCE"

    def test_universe_defaults(self) -> None:
        u = StrategySpecV2Universe(
            venue="BINANCE",
            instrument_id="BTCUSDT-PERP.BINANCE",
            timeframe="1-MINUTE",
        )
        assert u.asset_class is None
        assert u.market_type is None


class TestFeatureInputs:
    def test_orderbook_features(self) -> None:
        features = [
            FeatureInput(group=FeatureGroup.ORDERBOOK, name="best_bid"),
            FeatureInput(group=FeatureGroup.ORDERBOOK, name="spread_bps"),
            FeatureInput(group=FeatureGroup.ORDERBOOK, name="obi"),
        ]
        assert all(f.group == FeatureGroup.ORDERBOOK for f in features)

    def test_trades_features(self) -> None:
        f = FeatureInput(group=FeatureGroup.TRADES, name="cvd")
        assert f.group == FeatureGroup.TRADES

    def test_liquidation_features(self) -> None:
        f = FeatureInput(group=FeatureGroup.LIQUIDATION, name="cascade_score")
        assert f.group == FeatureGroup.LIQUIDATION

    def test_funding_features(self) -> None:
        f = FeatureInput(group=FeatureGroup.FUNDING, name="rate")
        assert f.group == FeatureGroup.FUNDING

    def test_svp_features(self) -> None:
        f = FeatureInput(group=FeatureGroup.SVP, name="poc")
        assert f.group == FeatureGroup.SVP

    def test_vwap_features(self) -> None:
        f = FeatureInput(group=FeatureGroup.VWAP, name="session")
        assert f.group == FeatureGroup.VWAP

    def test_source_health_features(self) -> None:
        f = FeatureInput(group=FeatureGroup.SOURCE_HEALTH, name="stale")
        assert f.group == FeatureGroup.SOURCE_HEALTH


class TestConditionDSL:
    def test_compare_condition(self) -> None:
        c = ConditionDSL(
            primitive=ConditionPrimitive.COMPARE,
            operands=["obi", ">", "0.3"],
        )
        assert c.primitive == ConditionPrimitive.COMPARE

    def test_cross_above(self) -> None:
        c = ConditionDSL(primitive=ConditionPrimitive.CROSS_ABOVE, operands=["cvd", "0"])
        assert c.primitive == ConditionPrimitive.CROSS_ABOVE

    def test_all_of_composite(self) -> None:
        c = ConditionDSL(
            primitive=ConditionPrimitive.ALL_OF,
            operands=[
                ConditionDSL(primitive=ConditionPrimitive.COMPARE, operands=["obi", ">", "0.3"]),
                ConditionDSL(primitive=ConditionPrimitive.COMPARE, operands=["spread_bps", "<", "5"]),
            ],
        )
        assert c.primitive == ConditionPrimitive.ALL_OF

    def test_stale_block(self) -> None:
        c = ConditionDSL(primitive=ConditionPrimitive.STALE_BLOCK, operands=["orderbook"])
        assert c.primitive == ConditionPrimitive.STALE_BLOCK


class TestEventDetectors:
    def test_absorption_detector(self) -> None:
        d = EventDetector(name="absorption_detected")
        assert d.name == "absorption_detected"

    def test_cvd_divergence_detector(self) -> None:
        d = EventDetector(name="cvd_divergence_detected")
        assert d.name == "cvd_divergence_detected"


class TestArchetypesAndOverlays:
    def test_absorption_reversal_archetype(self) -> None:
        a = Archetype(name="absorption_reversal")
        assert a.name == "absorption_reversal"

    def test_vwap_overlay(self) -> None:
        o = Overlay(name="vwap_value_reversion")
        assert o.name == "vwap_value_reversion"


class TestRiskContractV2:
    def test_risk_contract_fields(self) -> None:
        r = RiskContractV2(
            max_spread_bps=5.0,
            max_position_notional=10000.0,
            max_daily_loss=500.0,
        )
        assert r.max_spread_bps == 5.0
        assert r.max_position_notional == 10000.0

    def test_risk_contract_defaults(self) -> None:
        r = RiskContractV2(
            max_spread_bps=5.0,
            max_position_notional=10000.0,
            max_daily_loss=500.0,
        )
        assert r.max_slippage_bps is None
        assert r.cooldown_after_loss is None


class TestEvidenceRequirement:
    def test_evidence_fields(self) -> None:
        e = EvidenceRequirement(
            required_feature_hash="abc123",
            required_backtest_result_ref="bt_001",
        )
        assert e.required_feature_hash == "abc123"


class TestStrategySpecV2:
    def _make_spec(self) -> StrategySpecV2:
        return StrategySpecV2(
            metadata=StrategySpecV2Metadata(
                strategy_id="strat_001",
                lineage_id="lineage_001",
                name="ND Absorption Reversal",
                version="1.0.0",
                schema_version=SchemaVersion.V2,
                created_by="user",
            ),
            universe=StrategySpecV2Universe(
                venue="BINANCE",
                instrument_id="BTCUSDT-PERP.BINANCE",
                timeframe="1-MINUTE",
            ),
            feature_inputs=[
                FeatureInput(group=FeatureGroup.ORDERBOOK, name="obi"),
                FeatureInput(group=FeatureGroup.ORDERBOOK, name="spread_bps"),
                FeatureInput(group=FeatureGroup.TRADES, name="cvd"),
            ],
            conditions=[
                ConditionDSL(primitive=ConditionPrimitive.COMPARE, operands=["obi", ">", "0.3"]),
            ],
            risk_contract=RiskContractV2(
                max_spread_bps=5.0,
                max_position_notional=10000.0,
                max_daily_loss=500.0,
            ),
        )

    def test_full_spec_construction(self) -> None:
        spec = self._make_spec()
        assert spec.metadata.strategy_id == "strat_001"
        assert spec.universe.venue == "BINANCE"
        assert len(spec.feature_inputs) == 3
        assert spec.execution_authority is False

    def test_spec_no_execution_authority(self) -> None:
        spec = self._make_spec()
        assert spec.execution_authority is False

    def test_spec_optional_event_detectors(self) -> None:
        spec = self._make_spec()
        spec.event_detectors = [EventDetector(name="absorption_detected")]
        assert len(spec.event_detectors) == 1

    def test_spec_optional_archetype(self) -> None:
        spec = self._make_spec()
        spec.archetype = Archetype(name="absorption_reversal")
        assert spec.archetype.name == "absorption_reversal"

    def test_spec_schema_export(self) -> None:
        spec = self._make_spec()
        json_str = spec.model_dump_json()
        assert "strat_001" in json_str
        assert "BINANCE" in json_str

    def test_spec_json_round_trip(self) -> None:
        spec = self._make_spec()
        json_str = spec.model_dump_json()
        restored = StrategySpecV2.model_validate_json(json_str)
        assert restored.metadata.strategy_id == spec.metadata.strategy_id
        assert restored.universe.venue == spec.universe.venue
