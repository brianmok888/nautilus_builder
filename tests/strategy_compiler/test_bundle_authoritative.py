"""Tests for compiler v2 bundle being authoritative — v6 Segment 06.

Verifies:
- compile_strategy_spec_bundle is exported from __init__
- FullArtifactBundle is exported from __init__
- Static scan is integrated into bundle compilation
- Compile report includes static_scan_passed field
"""
from __future__ import annotations


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


class TestCompilerExports:
    def test_compile_strategy_spec_bundle_exported(self):
        from packages.strategy_compiler import compile_strategy_spec_bundle
        assert callable(compile_strategy_spec_bundle)

    def test_full_artifact_bundle_exported(self):
        from packages.strategy_compiler import FullArtifactBundle
        assert FullArtifactBundle is not None


class TestBundleStaticScan:
    def test_bundle_passes_static_scan(self):
        from packages.strategy_compiler.compiler import compile_strategy_spec_bundle
        from packages.strategy_compiler.static_scan import scan_generated_artifact
        bundle = compile_strategy_spec_bundle(_classic_payload(), profile="backtest")
        ir = bundle["compiled_strategy_ir"]
        ir_str = str(ir)
        result = scan_generated_artifact(ir_str)
        assert result.passed, f"Static scan violations: {result.violations}"

    def test_bundle_reports_execution_authority_false(self):
        from packages.strategy_compiler.compiler import compile_strategy_spec_bundle
        bundle = compile_strategy_spec_bundle(_classic_payload(), profile="backtest")
        manifest = bundle["artifact_bundle_manifest"]
        assert manifest["execution_authority"] is False

    def test_bundle_compile_report_has_static_scan_field(self):
        """Compile report must include a static_scan_passed field."""
        from packages.strategy_compiler.compiler import compile_strategy_spec_bundle
        bundle = compile_strategy_spec_bundle(_classic_payload(), profile="backtest")
        report = bundle["compile_report"]
        assert "static_scan_passed" in report
        assert report["static_scan_passed"] is True


class TestBundleDeterministicHash:
    def test_same_input_same_hash(self):
        from packages.strategy_compiler.compiler import compile_strategy_spec_bundle
        b1 = compile_strategy_spec_bundle(_classic_payload(), profile="backtest")
        b2 = compile_strategy_spec_bundle(_classic_payload(), profile="backtest")
        assert b1["artifact_bundle_manifest"]["artifact_bundle_hash"] == \
               b2["artifact_bundle_manifest"]["artifact_bundle_hash"]

    def test_different_input_different_hash(self):
        from packages.strategy_compiler.compiler import compile_strategy_spec_bundle
        p1 = _classic_payload()
        p2 = {**_classic_payload(), "instrument_id": "ETHUSDT-PERP.BINANCE"}
        b1 = compile_strategy_spec_bundle(p1, profile="backtest")
        b2 = compile_strategy_spec_bundle(p2, profile="backtest")
        assert b1["artifact_bundle_manifest"]["artifact_bundle_hash"] != \
               b2["artifact_bundle_manifest"]["artifact_bundle_hash"]
