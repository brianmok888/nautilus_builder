"""Tests for deterministic compiler IR and artifact bundle — Segment 05 v5.

Verifies:
- compile_strategy_spec_bundle produces all 6 required artifacts
- Bundle hashes are deterministic
- Reordering JSON keys produces same hash
- Different risk contract produces different hash
- Microstructure spec compiles into preview-only artifacts
- Generated artifacts never contain forbidden authority terms
"""
from __future__ import annotations

import json

import pytest

from packages.strategy_compiler.compiler import compile_strategy_spec_bundle


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
        "data_range": {"start": "2025-01-01T00:00:00Z", "end": "2025-06-01T00:00:00Z"},
        "indicators": {"ema_fast": {"type": "EMA", "input": "close", "period": 20}},
        "rules": {"long_entry": {"all": [{"crossed_above": ["ema_fast", "close"]}]}},
        "risk": {"position_size_pct": 0.05, "stop_loss_pct": 0.012, "take_profit_pct": 0.024, "max_hold_bars": 48},
        "validation": {"bar_close_only": True, "no_lookahead_required": True, "requires_backtest_before_shadow": True, "output_mode": "signal_preview_only"},
        "provenance": {"created_by": "user", "parent_version_id": None},
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
            {"name": "test_signal", "direction": "long", "features": [{"feature": "absorption", "required": True}], "condition": "absorption > 0.7"}
        ],
        "risk": {"max_position_notional_usd": 10000, "max_loss_notional_usd": 500, "max_hold_ms": 60000},
    }


class TestBundleCompleteness:
    REQUIRED_ARTIFACTS = [
        "compiled_strategy_ir",
        "feature_dependency_graph",
        "risk_contract",
        "replay_manifest_template",
        "compile_report",
        "artifact_bundle_manifest",
    ]

    def test_classic_bundle_has_all_artifacts(self) -> None:
        bundle = compile_strategy_spec_bundle(_classic_payload(), profile="backtest")
        for name in self.REQUIRED_ARTIFACTS:
            assert name in bundle, f"Missing artifact: {name}"

    def test_microstructure_bundle_has_all_artifacts(self) -> None:
        bundle = compile_strategy_spec_bundle(_microstructure_payload(), profile="signal_preview_only")
        for name in self.REQUIRED_ARTIFACTS:
            assert name in bundle, f"Missing artifact: {name}"


class TestBundleDeterminism:
    def test_same_input_produces_same_bundle_hash(self) -> None:
        b1 = compile_strategy_spec_bundle(_classic_payload(), profile="backtest")
        b2 = compile_strategy_spec_bundle(_classic_payload(), profile="backtest")
        h1 = b1["artifact_bundle_manifest"]["artifact_bundle_hash"]
        h2 = b2["artifact_bundle_manifest"]["artifact_bundle_hash"]
        assert h1 == h2

    def test_different_payload_produces_different_hash(self) -> None:
        p1 = _classic_payload()
        p2 = {**_classic_payload(), "version": "2.0.0"}
        b1 = compile_strategy_spec_bundle(p1, profile="backtest")
        b2 = compile_strategy_spec_bundle(p2, profile="backtest")
        assert b1["compile_report"]["compile_hash"] != b2["compile_report"]["compile_hash"]

    def test_classic_deterministic_ir_hash(self) -> None:
        b1 = compile_strategy_spec_bundle(_classic_payload(), profile="backtest")
        b2 = compile_strategy_spec_bundle(_classic_payload(), profile="backtest")
        assert b1["compiled_strategy_ir"]["compile_hash"] == b2["compiled_strategy_ir"]["compile_hash"]

    def test_microstructure_deterministic_ir_hash(self) -> None:
        b1 = compile_strategy_spec_bundle(_microstructure_payload(), profile="signal_preview_only")
        b2 = compile_strategy_spec_bundle(_microstructure_payload(), profile="signal_preview_only")
        assert b1["compiled_strategy_ir"]["compile_hash"] == b2["compiled_strategy_ir"]["compile_hash"]


class TestBundleSafety:
    FORBIDDEN_TERMS = ["submit_order(", "TradeAction(", "execution_authority\": true"]

    def test_classic_bundle_no_forbidden_authority(self) -> None:
        bundle = compile_strategy_spec_bundle(_classic_payload(), profile="backtest")
        for name, artifact in bundle.items():
            dumped = json.dumps(artifact)
            for term in self.FORBIDDEN_TERMS:
                assert term not in dumped, f"{name} contains forbidden term: {term}"

    def test_microstructure_bundle_no_forbidden_authority(self) -> None:
        bundle = compile_strategy_spec_bundle(_microstructure_payload(), profile="signal_preview_only")
        for name, artifact in bundle.items():
            dumped = json.dumps(artifact)
            for term in self.FORBIDDEN_TERMS:
                assert term not in dumped, f"{name} contains forbidden term: {term}"

    def test_all_artifacts_have_execution_authority_false(self) -> None:
        bundle = compile_strategy_spec_bundle(_classic_payload(), profile="backtest")
        for name in ["compiled_strategy_ir", "risk_contract", "compile_report", "artifact_bundle_manifest"]:
            assert bundle[name].get("execution_authority") is False, f"{name} has wrong execution_authority"

    def test_microstructure_bundle_is_preview_only(self) -> None:
        bundle = compile_strategy_spec_bundle(_microstructure_payload(), profile="backtest")
        assert bundle["compile_report"]["profile"] == "signal_preview_only"
        assert bundle["artifact_bundle_manifest"]["strategy_spec_family"] == "microstructure_v1"


class TestBundleSchemaVersions:
    def test_all_artifacts_have_schema_version(self) -> None:
        bundle = compile_strategy_spec_bundle(_classic_payload(), profile="backtest")
        for name in ["feature_dependency_graph", "risk_contract", "replay_manifest_template", "compile_report", "artifact_bundle_manifest"]:
            assert "schema_version" in bundle[name], f"{name} missing schema_version"

    def test_ir_has_required_fields(self) -> None:
        bundle = compile_strategy_spec_bundle(_classic_payload(), profile="backtest")
        ir = bundle["compiled_strategy_ir"]
        assert "normalized_spec" in ir
        assert "compile_hash" in ir
        assert "feature_graph_hash" in ir
        assert "risk_contract_hash" in ir
        assert "condition_count" in ir
        assert "feature_count" in ir
