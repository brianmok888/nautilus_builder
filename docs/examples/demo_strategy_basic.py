#!/usr/bin/env python3
"""Demo: Create a basic StrategySpec, validate it, and compile it.

This is the simplest possible end-to-end demo of the Nautilus Builder pipeline.
Run from repo root: python3 docs/examples/demo_strategy_basic.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

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
from packages.strategy_compiler.compiler import compile_strategy_spec
from packages.strategy_validation.validators import validate_strategy_spec


def main() -> None:
    print("=" * 60)
    print("Demo: Basic StrategySpec -> Validate -> Compile")
    print("=" * 60)

    # ── 1. Create a minimal StrategySpec ────────────────────────
    spec = StrategySpec(
        schema_version="1.0",
        version="0.1.0",
        stage=StrategyStage.DRAFT,
        status=StrategyStatus.DRAFT,
        created_from=CreatedFrom.USER,
        adapter_id="binance",
        venue="BINANCE",
        instrument_id="BTCUSDT-PERP.BINANCE",
        bar_type="BTCUSDT-PERP.BINANCE-5-MINUTE-LAST-EXTERNAL",
        data_range=DataRange(start="2024-01-01T00:00:00Z", end="2024-06-01T00:00:00Z"),
        indicators={
            "ema_fast": IndicatorSpec(type=IndicatorType.EMA, input=IndicatorInput.CLOSE, period=10),
            "ema_slow": IndicatorSpec(type=IndicatorType.EMA, input=IndicatorInput.CLOSE, period=20),
        },
        rules={
            "entry_long": RuleBlock(
                all=[RuleClause(crossed_above=["ema_fast", "ema_slow"])],
            ),
            "exit_long": RuleBlock(
                all=[RuleClause(crossed_below=["ema_fast", "ema_slow"])],
            ),
        },
        risk=RiskBlock(
            position_size_pct=0.02,
            stop_loss_pct=0.05,
            take_profit_pct=0.10,
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

    print(f"\nStrategySpec created: {spec.version}")
    print(f"   Instrument: {spec.instrument_id}")
    print(f"   Indicators: {list(spec.indicators.keys())}")
    print(f"   Rules: {list(spec.rules.keys())}")

    # ── 2. Validate ─────────────────────────────────────────────
    report = validate_strategy_spec(spec.model_dump(mode="json"))
    print(f"\nValidation: {'PASSED' if report.is_valid else 'FAILED'}")
    if report.errors:
        for err in report.errors:
            print(f"   ERROR: {err}")
    if report.warnings:
        for warn in report.warnings:
            print(f"   WARN: {warn}")
    if report.is_valid:
        print("   All checks passed.")

    # ── 3. Compile ──────────────────────────────────────────────
    artifact = compile_strategy_spec(spec.model_dump(mode="json"), profile="backtest")
    print(f"\nCompiled: {artifact.profile}")
    print(f"   Class: {artifact.strategy_class}")
    print(f"   Authority: {artifact.execution_authority}")
    print(f"   Hash: {artifact.compile_hash[:16]}...")

    # ── 4. Serialize ────────────────────────────────────────────
    payload = spec.model_dump(mode="json")
    print(f"\nJSON payload ({len(json.dumps(payload))} bytes)")
    print(f"   Keys: {list(payload.keys())}")

    print("\n" + "=" * 60)
    print("Demo complete. Strategy is valid and compiled.")
    print("=" * 60)


if __name__ == "__main__":
    main()
