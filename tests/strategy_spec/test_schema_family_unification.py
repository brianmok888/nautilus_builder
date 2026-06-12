"""Tests for StrategySpec schema family unification — Segment 04 v5.

Verifies:
- parse_strategy_spec handles both families
- Compiler handles both families
- Microstructure spec cannot set execution_authority
- Source health validation blocks compile on missing features
- Classic spec remains backward compatible
- JSON schemas export for both families
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from packages.strategy_spec.microstructure import (
    FeatureSourceHealth,
    MicrostructureFeature,
    SourceHealth,
    StrategySpecMicrostructureV1,
)
from packages.strategy_spec.models import StrategySpec as StrategySpecClassicV1
from packages.strategy_spec.resolver import get_spec_family_name, parse_strategy_spec
from packages.strategy_compiler.compiler import compile_strategy_spec


def _classic_payload() -> dict:
    return {
        "schema_version": "1.0.0",
        "version": "1.0.0",
        "stage": "draft",
        "status": "draft",
        "created_from": "user",
        "adapter_id": "binance",
        "venue": "BINANCE",
        "instrument_id": "BTCUSDT-PERP.BINANCE",
        "bar_type": "BTCUSDT-PERP.BINANCE-5-MINUTE-LAST-EXTERNAL",
        "data_range": {
            "start": "2025-01-01T00:00:00Z",
            "end": "2025-06-01T00:00:00Z",
        },
        "indicators": {
            "ema_fast": {"type": "EMA", "input": "close", "period": 20},
        },
        "rules": {
            "long_entry": {
                "all": [
                    {"crossed_above": ["ema_fast", "close"]},
                ]
            },
        },
        "risk": {
            "position_size_pct": 0.05,
            "stop_loss_pct": 0.012,
            "take_profit_pct": 0.024,
            "max_hold_bars": 48,
        },
        "validation": {
            "bar_close_only": True,
            "no_lookahead_required": True,
            "requires_backtest_before_shadow": True,
            "output_mode": "signal_preview_only",
        },
        "provenance": {
            "created_by": "user",
            "parent_version_id": None,
        },
    }


def _microstructure_payload() -> dict:
    return {
        "schema_version": "microstructure_v1",
        "version": "1.0.0",
        "adapter_id": "binance",
        "venue": "BINANCE",
        "instrument_id": "BTCUSDT-PERP.BINANCE",
        "features": [
            {"feature": "absorption", "required": True, "fail_closed_on_missing": True},
            {"feature": "cvd", "required": True, "max_staleness_ms": 5000},
        ],
        "signals": [
            {
                "name": "test_signal",
                "direction": "long",
                "features": [
                    {"feature": "absorption", "required": True},
                ],
                "condition": "absorption > 0.7 AND cvd < -1000000",
            }
        ],
        "risk": {
            "max_position_notional_usd": 10000,
            "max_loss_notional_usd": 500,
            "max_hold_ms": 60000,
        },
    }


class TestSpecFamilyResolver:
    def test_classic_spec_parses_without_schema_version(self) -> None:
        spec = parse_strategy_spec(_classic_payload())
        assert isinstance(spec, StrategySpecClassicV1)

    def test_microstructure_spec_parses_with_schema_version(self) -> None:
        spec = parse_strategy_spec(_microstructure_payload())
        assert isinstance(spec, StrategySpecMicrostructureV1)

    def test_family_name_classic(self) -> None:
        assert get_spec_family_name(_classic_payload()) == "classic_v1"

    def test_family_name_microstructure(self) -> None:
        assert get_spec_family_name(_microstructure_payload()) == "microstructure_v1"


class TestCompilerSchemaFamilies:
    def test_classic_spec_compiles_backtest(self) -> None:
        artifact = compile_strategy_spec(_classic_payload(), profile="backtest")
        assert artifact.profile == "backtest"
        assert artifact.execution_authority is False

    def test_classic_spec_compiles_signal_preview(self) -> None:
        artifact = compile_strategy_spec(_classic_payload(), profile="signal_preview_only")
        assert artifact.profile == "signal_preview_only"
        assert artifact.execution_authority is False

    def test_microstructure_spec_compiles_signal_preview(self) -> None:
        artifact = compile_strategy_spec(_microstructure_payload(), profile="signal_preview_only")
        assert artifact.profile == "signal_preview_only"
        assert artifact.execution_authority is False
        assert artifact.strategy_class == "RuleGraphMicrostructureStrategy"

    def test_microstructure_spec_compiles_to_signal_preview_even_with_backtest_profile(self) -> None:
        """Microstructure always compiles to signal_preview_only regardless of profile."""
        artifact = compile_strategy_spec(_microstructure_payload(), profile="backtest")
        assert artifact.profile == "signal_preview_only"
        assert artifact.execution_authority is False

    def test_deterministic_hash_classic(self) -> None:
        a1 = compile_strategy_spec(_classic_payload(), profile="backtest")
        a2 = compile_strategy_spec(_classic_payload(), profile="backtest")
        assert a1.compile_hash == a2.compile_hash

    def test_deterministic_hash_microstructure(self) -> None:
        a1 = compile_strategy_spec(_microstructure_payload(), profile="signal_preview_only")
        a2 = compile_strategy_spec(_microstructure_payload(), profile="signal_preview_only")
        assert a1.compile_hash == a2.compile_hash


class TestMicrostructureExecutionAuthority:
    def test_microstructure_spec_cannot_set_execution_authority(self) -> None:
        payload = _microstructure_payload()
        payload["execution_authority"] = True
        with pytest.raises(Exception):
            parse_strategy_spec(payload)

    def test_microstructure_spec_cannot_set_live_output_mode(self) -> None:
        payload = _microstructure_payload()
        payload["output_mode"] = "live_execution"
        with pytest.raises(Exception):
            parse_strategy_spec(payload)


class TestMicrostructureSourceHealth:
    def test_missing_required_feature_blocks_validation(self) -> None:
        spec = parse_strategy_spec(_microstructure_payload())
        assert isinstance(spec, StrategySpecMicrostructureV1)
        health_records = [
            FeatureSourceHealth(
                feature=MicrostructureFeature.CVD,
                source_available=True,
                missing=False,
                stale=False,
            )
            # Note: absorption has no health record
        ]
        violations = spec.validate_source_health(health_records)
        assert any("absorption" in v and "no health record" in v for v in violations)

    def test_stale_required_feature_blocks_validation(self) -> None:
        spec = parse_strategy_spec(_microstructure_payload())
        assert isinstance(spec, StrategySpecMicrostructureV1)
        health_records = [
            FeatureSourceHealth(
                feature=MicrostructureFeature.ABSORPTION,
                source_available=True,
                missing=False,
                stale=False,
            ),
            FeatureSourceHealth(
                feature=MicrostructureFeature.CVD,
                source_available=True,
                missing=False,
                stale=True,
                age_ms=10000,
            ),
        ]
        violations = spec.validate_source_health(health_records)
        assert any("cvd" in v and "stale" in v for v in violations)

    def test_healthy_features_pass_validation(self) -> None:
        spec = parse_strategy_spec(_microstructure_payload())
        assert isinstance(spec, StrategySpecMicrostructureV1)
        health_records = [
            FeatureSourceHealth(
                feature=MicrostructureFeature.ABSORPTION,
                source_available=True,
                missing=False,
                stale=False,
            ),
            FeatureSourceHealth(
                feature=MicrostructureFeature.CVD,
                source_available=True,
                missing=False,
                stale=False,
            ),
        ]
        violations = spec.validate_source_health(health_records)
        assert violations == []


class TestSchemaExport:
    def test_export_classic_v1_schema(self) -> None:
        from packages.strategy_spec.schema_export import export_classic_v1_schema

        schema = export_classic_v1_schema()
        assert isinstance(schema, dict)
        assert "properties" in schema

    def test_export_microstructure_v1_schema(self) -> None:
        from packages.strategy_spec.schema_export import export_microstructure_v1_schema

        schema = export_microstructure_v1_schema()
        assert isinstance(schema, dict)
        assert "properties" in schema

    def test_write_schemas_to_dir(self, tmp_path: Path) -> None:
        from packages.strategy_spec.schema_export import write_schemas_to_dir

        paths = write_schemas_to_dir(tmp_path)
        assert "classic_v1" in paths
        assert "microstructure_v1" in paths
        # Verify files are valid JSON
        for path in paths.values():
            data = json.loads(path.read_text())
            assert isinstance(data, dict)


class TestExampleSpecs:
    def test_example_specs_parse_successfully(self) -> None:
        """All example spec files must parse into the correct family."""
        examples_dir = Path(__file__).resolve().parents[2] / "packages" / "strategy_spec" / "examples"
        if not examples_dir.exists():
            pytest.skip("No examples directory")

        for path in sorted(examples_dir.glob("*.json")):
            payload = json.loads(path.read_text())
            spec = parse_strategy_spec(payload)
            assert isinstance(spec, (StrategySpecClassicV1, StrategySpecMicrostructureV1))
            if "microstructure" in path.name:
                assert isinstance(spec, StrategySpecMicrostructureV1)
                assert spec.execution_authority is False
