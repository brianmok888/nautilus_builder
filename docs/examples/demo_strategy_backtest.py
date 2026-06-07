#!/usr/bin/env python3
"""Demo: Full pipeline — StrategySpec -> Validate -> Compile -> Backtest Config.

Exercises the full Nautilus Builder pipeline from spec creation through
backtest configuration generation. No live trading or venue connection required.
Run from repo root: python3 docs/examples/demo_strategy_backtest.py
"""
from __future__ import annotations

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
from packages.backtest_runner.config_builder import build_backtest_config
from packages.backtest_runner.engine_contract import NAUTILUS_TRADER_VERSION


def main() -> None:
    print("=" * 60)
    print("Demo: Full Pipeline -> Backtest Config")
    print("=" * 60)

    # ── 1. Create StrategySpec ──────────────────────────────────
    spec = StrategySpec(
        schema_version="1.0",
        version="0.2.0",
        stage=StrategyStage.TESTING,
        status=StrategyStatus.VALIDATED,
        created_from=CreatedFrom.USER,
        adapter_id="binance",
        venue="BINANCE",
        instrument_id="ETHUSDT-PERP.BINANCE",
        bar_type="ETHUSDT-PERP.BINANCE-15-MINUTE-LAST-EXTERNAL",
        data_range=DataRange(start="2024-03-01T00:00:00Z", end="2024-09-01T00:00:00Z"),
        indicators={
            "rsi": IndicatorSpec(type=IndicatorType.RSI, input=IndicatorInput.CLOSE, period=14),
            "ema_trend": IndicatorSpec(type=IndicatorType.EMA, input=IndicatorInput.CLOSE, period=50),
        },
        rules={
            "oversold_entry": RuleBlock(
                all=[RuleClause(lt=["rsi", 30])],
            ),
            "overbought_exit": RuleBlock(
                all=[RuleClause(gt=["rsi", 70])],
            ),
        },
        risk=RiskBlock(
            position_size_pct=0.01,
            stop_loss_pct=0.03,
            take_profit_pct=0.06,
            max_hold_bars=120,
        ),
        validation=ValidationFlags(
            bar_close_only=True,
            no_lookahead_required=True,
            requires_backtest_before_shadow=True,
            output_mode=OutputMode.SIGNAL_PREVIEW_ONLY,
        ),
        provenance=Provenance(created_by=CreatedFrom.USER),
    )

    print(f"\n1. StrategySpec created: v{spec.version}")
    print(f"   Stage: {spec.stage.value}")
    print(f"   Instrument: {spec.instrument_id}")

    # ── 2. Validate ─────────────────────────────────────────────
    payload = spec.model_dump(mode="json")
    report = validate_strategy_spec(payload)
    print(f"\n2. Validation: {'PASSED' if report.is_valid else 'FAILED'}")
    if not report.is_valid:
        for err in report.errors:
            print(f"   ERROR: {err}")
        sys.exit(1)

    # ── 3. Compile ──────────────────────────────────────────────
    artifact = compile_strategy_spec(payload, profile="backtest")
    print(f"\n3. Compiled: {artifact.profile}")
    print(f"   Strategy class: {artifact.strategy_class}")
    print(f"   Execution authority: {artifact.execution_authority}")
    print(f"   Compile hash: {artifact.compile_hash[:16]}...")

    # ── 4. Build backtest config ────────────────────────────────
    backtest_config = build_backtest_config(
        strategy_spec_version=spec.version,
        adapter_id=spec.adapter_id,
        instrument_id=spec.instrument_id,
        compile_hash=artifact.compile_hash,
        validation_report_id="demo-val-001",
        worker_image="nautilus-builder-worker:latest",
    )
    print("\n4. Backtest config:")
    print(f"   NT version: {backtest_config['nautilus_trader_version']}")
    print(f"   Engine mode: {backtest_config['engine_mode']}")
    print(f"   Live trading: {backtest_config['live_trading_enabled']}")
    print(f"   Trade execution: {backtest_config['trade_execution']}")
    print(f"   Execution authority: {backtest_config['execution_authority']}")

    # ── 5. Summary ──────────────────────────────────────────────
    print(f"\n{'=' * 60}")
    print("Pipeline summary:")
    print(f"  NT version aligned: {backtest_config['nautilus_trader_version'] == NAUTILUS_TRADER_VERSION}")
    print(f"  No credentials in config: {'credentials' not in backtest_config}")
    print(f"  Execution authority: {backtest_config['execution_authority']}")
    print(f"  Config keys: {sorted(backtest_config.keys())}")
    print("=" * 60)
    print("Demo complete. Full pipeline exercised successfully.")


if __name__ == "__main__":
    main()
