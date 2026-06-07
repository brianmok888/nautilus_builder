"""POST /api/pipeline/run — one-shot end-to-end pipeline for the Web UI.

Accepts a StrategySpec JSON payload, validates, compiles, runs backtest,
and returns the full result in a single response. This is the web-equivalent
of scripts/run_backtest.py.
"""
from __future__ import annotations

from packages.strategy_spec.models import StrategySpec
from packages.strategy_compiler.compiler import compile_strategy_spec
from packages.strategy_validation.validators import validate_strategy_spec
from packages.backtest_runner.runner import run_backtest_fixture
from packages.backtest_runner.engine_contract import NAUTILUS_TRADER_VERSION
from services.api.router import ApiResponse


def pipeline_run_payload(payload: dict) -> ApiResponse:
    """Run the full pipeline on a StrategySpec payload.

    Chains: parse → validate → compile → backtest → result.
    Returns 200 on success, 422 on validation/parse failures.
    """
    # ── Step 1: Parse as StrategySpec ────────────────────────────
    try:
        spec = StrategySpec.model_validate(payload)
    except Exception as exc:
        return ApiResponse(
            {"error": "invalid_spec", "details": str(exc)},
            status_code=422,
        )

    # ── Step 2: Validate ─────────────────────────────────────────
    report = validate_strategy_spec(payload)
    if not report.is_valid:
        return ApiResponse(
            {
                "error": "validation_failed",
                "is_valid": False,
                "validation_errors": report.errors,
                "spec_version": spec.version,
                "instrument_id": spec.instrument_id,
            },
            status_code=422,
        )

    # ── Step 3: Compile ──────────────────────────────────────────
    artifact = compile_strategy_spec(payload, profile="backtest")

    # ── Step 4: Run backtest (fixture mode) ───────────────────────
    backtest_result = run_backtest_fixture(
        strategy_spec_version=spec.version,
        adapter_id=spec.adapter_id,
        instrument_id=spec.instrument_id,
        compile_hash=artifact.compile_hash,
        worker_image="nautilus-builder-worker:latest",
    )

    # ── Step 5: Build response ───────────────────────────────────
    metrics = backtest_result.summary_metrics
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
        "summary_metrics": metrics,
        "total_trades": metrics.get("trade_count", 0),
        "total_return": metrics.get("total_return", 0.0),
        "artifact_refs": backtest_result.artifact_refs,
        "mode": "pipeline_run",
    }

    return ApiResponse(result, status_code=200)
