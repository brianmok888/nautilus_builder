"""StrategySpec v1-to-v2 migration tests — Segment 4."""
import pytest

from packages.strategy_spec.migration import migrate_v1_to_v2
from packages.strategy_spec.models import (
    CreatedFrom,
    DataRange,
    IndicatorInput,
    IndicatorSpec,
    IndicatorType,
    OutputMode,
    Provenance,
    RiskBlock,
    RuleBlock,
    RuleClause,
    StrategySpec,
    StrategyStage,
    StrategyStatus,
    ValidationFlags,
)


def _make_v1_spec() -> StrategySpec:
    return StrategySpec(
        schema_version="v1",
        version="1.0.0",
        stage=StrategyStage.DRAFT,
        status=StrategyStatus.DRAFT,
        created_from=CreatedFrom.USER,
        adapter_id="binance_adapter",
        venue="BINANCE",
        instrument_id="BTCUSDT-PERP.BINANCE",
        bar_type="BTCUSDT-PERP.BINANCE-5-MINUTE-LAST-EXTERNAL",
        data_range=DataRange(start="2024-01-01", end="2024-06-01"),
        indicators={
            "ema_fast": IndicatorSpec(type=IndicatorType.EMA, input=IndicatorInput.CLOSE, period=20),
            "ema_slow": IndicatorSpec(type=IndicatorType.EMA, input=IndicatorInput.CLOSE, period=50),
        },
        rules={
            "entry": RuleBlock(all=[
                RuleClause(crossed_above=["ema_fast", "ema_slow"]),
            ]),
        },
        risk=RiskBlock(
            position_size_pct=0.1,
            stop_loss_pct=0.02,
            take_profit_pct=0.04,
            max_hold_bars=60,
        ),
        validation=ValidationFlags(
            bar_close_only=True,
            no_lookahead_required=True,
            requires_backtest_before_shadow=True,
            output_mode=OutputMode.SIGNAL_PREVIEW_ONLY,
        ),
        provenance=Provenance(created_by=CreatedFrom.USER),
    )


class TestV1ToV2Migration:
    def test_migration_preserves_venue(self) -> None:
        v1 = _make_v1_spec()
        v2 = migrate_v1_to_v2(v1)
        assert v2.universe.venue == "BINANCE"

    def test_migration_preserves_instrument_id(self) -> None:
        v1 = _make_v1_spec()
        v2 = migrate_v1_to_v2(v1)
        assert v2.universe.instrument_id == "BTCUSDT-PERP.BINANCE"

    def test_migration_maps_indicators_to_features(self) -> None:
        v1 = _make_v1_spec()
        v2 = migrate_v1_to_v2(v1)
        assert len(v2.feature_inputs) == 2
        names = [f.name for f in v2.feature_inputs]
        assert "ema_fast" in names

    def test_migration_no_execution_authority(self) -> None:
        v1 = _make_v1_spec()
        v2 = migrate_v1_to_v2(v1)
        assert v2.execution_authority is False

    def test_migration_schema_version_is_v2(self) -> None:
        v1 = _make_v1_spec()
        v2 = migrate_v1_to_v2(v1)
        assert v2.metadata.schema_version == "v2"

    def test_migration_json_round_trip(self) -> None:
        v1 = _make_v1_spec()
        v2 = migrate_v1_to_v2(v1)
        json_str = v2.model_dump_json()
        from packages.strategy_spec.models_v2 import StrategySpecV2
        restored = StrategySpecV2.model_validate_json(json_str)
        assert restored.universe.venue == "BINANCE"

    def test_migration_preserves_created_by(self) -> None:
        v1 = _make_v1_spec()
        v2 = migrate_v1_to_v2(v1)
        assert v2.metadata.created_by == "user"
