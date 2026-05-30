#!/usr/bin/env python3
"""Run end-to-end backtest pipeline: spec -> validate -> compile -> backtest -> result.

Usage:
    python scripts/run_backtest.py --spec docs/examples/specs/dual_ma.json
    python scripts/run_backtest.py --spec docs/examples/specs/dual_ma.json --json
    python scripts/run_backtest.py --help

This chains all Builder seams into a single flow an operator can execute
and see results in under 30 seconds. No live trading or venue connection required.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

# Ensure repo root is importable
REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from packages.strategy_spec.models import StrategySpec
from packages.strategy_compiler.compiler import compile_strategy_spec
from packages.strategy_validation.validators import validate_strategy_spec
from packages.backtest_runner.runner import run_backtest_fixture
from packages.backtest_runner.engine_contract import NAUTILUS_TRADER_VERSION


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run end-to-end backtest pipeline: spec -> validate -> compile -> backtest -> result",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""\
Examples:
  python scripts/run_backtest.py --spec docs/examples/specs/dual_ma.json
  python scripts/run_backtest.py --spec docs/examples/specs/rsi_reversal.json --json
  python scripts/run_backtest.py --spec examples/my_strategy.json --output results/
""",
    )
    parser.add_argument(
        "--spec", required=True,
        help="Path to StrategySpec JSON file",
    )
    parser.add_argument(
        "--profile", default="backtest",
        choices=["backtest", "signal_preview_only"],
        help="Compile profile (default: backtest)",
    )
    parser.add_argument(
        "--output", default=None,
        help="Directory to write result artifact (default: stdout only)",
    )
    parser.add_argument(
        "--json", action="store_true",
        help="Output result as JSON to stdout",
    )
    return parser.parse_args()


def load_spec(spec_path: str) -> dict:
    path = Path(spec_path)
    if not path.is_file():
        print(f"ERROR: spec file not found: {spec_path}", file=sys.stderr)
        sys.exit(1)
    with open(path) as f:
        return json.load(f)


def run_pipeline(args: argparse.Namespace) -> dict:
    t0 = time.monotonic()

    # ── Step 1: Load and parse spec ────────────────────────────
    payload = load_spec(args.spec)
    spec = StrategySpec.model_validate(payload)
    elapsed_load = time.monotonic() - t0

    # ── Step 2: Validate ────────────────────────────────────────
    t1 = time.monotonic()
    report = validate_strategy_spec(payload)
    elapsed_validate = time.monotonic() - t1

    if not report.is_valid:
        errors = report.errors
        return {
            "is_valid": False,
            "validation_errors": errors,
            "spec_version": spec.version,
            "instrument_id": spec.instrument_id,
            "elapsed_total": time.monotonic() - t0,
        }

    # ── Step 3: Compile ─────────────────────────────────────────
    t2 = time.monotonic()
    artifact = compile_strategy_spec(payload, profile=args.profile)
    elapsed_compile = time.monotonic() - t2

    # ── Step 4: Run backtest (fixture mode — no venue needed) ───
    t3 = time.monotonic()
    backtest_result = run_backtest_fixture(
        strategy_spec_version=spec.version,
        adapter_id=spec.adapter_id,
        instrument_id=spec.instrument_id,
        compile_hash=artifact.compile_hash,
        worker_image="nautilus-builder-worker:latest",
    )
    elapsed_backtest = time.monotonic() - t3
    elapsed_total = time.monotonic() - t0

    # ── Extract result data ─────────────────────────────────────
    summary = backtest_result.report_summary
    metrics = backtest_result.summary_metrics
    equity_curve = metrics.get("equity_points", 0)
    total_trades = metrics.get("trade_count", 0)
    total_pnl = metrics.get("total_return", 0.0)

    # ── Build result ────────────────────────────────────────────
    result = {
        "is_valid": True,
        "validation_errors": [],
        "spec_version": spec.version,
        "instrument_id": spec.instrument_id,
        "stage": spec.stage.value,
        "adapter_id": spec.adapter_id,
        "indicators": list(spec.indicators.keys()),
        "rules": list(spec.rules.keys()),
        "compile_profile": artifact.profile,
        "strategy_class": artifact.strategy_class,
        "execution_authority": artifact.execution_authority,
        "compile_hash": artifact.compile_hash,
        "nt_version": NAUTILUS_TRADER_VERSION,
        "engine_mode": backtest_result.engine_mode,
        "backtest_job_id": backtest_result.backtest_job_id,
        "artifact_refs": backtest_result.artifact_refs,
        "summary_metrics": metrics,
        "total_trades": total_trades,
        "total_return": total_pnl,
        "elapsed": {
            "load": round(elapsed_load, 3),
            "validate": round(elapsed_validate, 3),
            "compile": round(elapsed_compile, 3),
            "backtest": round(elapsed_backtest, 3),
            "total": round(elapsed_total, 3),
        },
    }

    # ── Write output file if requested ─────────────────────────
    if args.output:
        out_dir = Path(args.output)
        out_dir.mkdir(parents=True, exist_ok=True)
        out_file = out_dir / f"backtest_{spec.version}_{artifact.compile_hash[:8]}.json"
        out_file.write_text(json.dumps(result, indent=2))
        result["output_file"] = str(out_file)

    return result


def print_human_report(result: dict) -> None:
    print("=" * 64)
    print("  Nautilus Builder — Backtest Pipeline Result")
    print("=" * 64)
    print(f"  Spec:        v{result['spec_version']}")
    print(f"  Instrument:  {result['instrument_id']}")
    print(f"  Adapter:     {result['adapter_id']}")
    print(f"  Indicators:  {', '.join(result.get('indicators', []))}")
    print(f"  Rules:       {', '.join(result.get('rules', []))}")
    print(f"  NT Version:  {result['nt_version']}")
    print()
    print(f"  Validation:  {'PASSED' if result['is_valid'] else 'FAILED'}")
    if result["validation_errors"]:
        for err in result["validation_errors"]:
            print(f"    ERROR: {err}")
    print()
    print(f"  Compile:     {result.get('compile_profile', 'N/A')}")
    print(f"  Class:       {result.get('strategy_class', 'N/A')}")
    print(f"  Authority:   {result.get('execution_authority', 'N/A')}")
    print(f"  Hash:        {result.get('compile_hash', 'N/A')[:16]}...")
    print()
    metrics = result.get("summary_metrics", {})
    print(f"  Backtest:")
    print(f"    Trades:    {result.get('total_trades', 0)}")
    print(f"    Return:    {result.get('total_return', 0):.4f}")
    for key, val in metrics.items():
        print(f"    {key}: {val}")
    print()
    elapsed = result.get("elapsed", {})
    print(f"  Timing:      {elapsed.get('total', 0):.3f}s total")
    print(f"               {elapsed.get('load', 0):.3f}s load, "
          f"{elapsed.get('validate', 0):.3f}s validate, "
          f"{elapsed.get('compile', 0):.3f}s compile, "
          f"{elapsed.get('backtest', 0):.3f}s backtest")
    if "output_file" in result:
        print(f"  Output:      {result['output_file']}")
    print("=" * 64)
    print("  Pipeline complete." if result["is_valid"] else "  Pipeline FAILED.")
    print("=" * 64)


def main() -> None:
    args = parse_args()
    result = run_pipeline(args)

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print_human_report(result)

    sys.exit(0 if result["is_valid"] else 1)


if __name__ == "__main__":
    main()
