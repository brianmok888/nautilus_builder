"""Seed demo backtest evidence for Nautilus Builder demo strategies.

This script is idempotent — running it twice will not duplicate records.

It creates demo backtest jobs that show realistic lifecycle states:
  - demo_compiled: backtest job created but not yet run
  - demo_replay_failed: backtest job that failed
  - demo_replay_passed: backtest job that succeeded with report artifacts
  - demo_promotion_requested: replay_passed + promotion-requested audit context
  - demo_promotion_ready: replay_passed + approved/execution_ready status

This script is read-only with respect to authority: it does not submit orders,
create TradeAction, modify StrategySpec semantics, or grant live execution.

Usage:
    uv run python scripts/seed_demo_evidence.py
"""
from __future__ import annotations

import os
import sys

# Ensure the project root is on sys.path when invoked as a script.
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from packages.backtest_jobs.service import BacktestJobService  # noqa: E402
from packages.auth import UserProjectContext  # noqa: E402
from packages.strategy_spec.demo_seed import seed_demo_strategies  # noqa: E402
from packages.strategy_spec.repository import InMemoryStrategyRepository  # noqa: E402


# Deterministic demo hashes (not real secrets).
_DEMO_COMPILE_HASH = "sha256:demo_compile_001"
_DEMO_COMPILE_HASH_REPLAY = "sha256:demo_compile_002"
_DEMO_REPORT_HASH = "sha256:demo_replay_report_001"


def seed_demo_evidence(
    repository: InMemoryStrategyRepository,
    backtest_service: BacktestJobService,
    *,
    context: UserProjectContext | None = None,
) -> dict[str, str]:
    """Seed demo backtest evidence for the demo strategies.

    Returns a mapping of strategy_id -> job_id (or "" if no job created).
    Idempotent: re-running returns existing jobs.
    """
    seed_demo_strategies(repository, context=context)
    scope_payload = _scope_payload(context)
    detail = repository.detail("demo_compiled")
    compiled_version_id = ""
    if detail is not None:
        versions = detail.get("versions", [])
        if versions:
            compiled_version_id = versions[-1].get("strategy_version_id", "")  # type: ignore[union-attr]

    result: dict[str, str] = {}

    # demo_compiled — a backtest job created but not yet run (compile evidence present, no replay result)
    if compiled_version_id:
        job_compiled = backtest_service.create_job({
            "strategy_spec_version_id": compiled_version_id,
            "adapter_profile_id": "BINANCE_PERP",
            "instrument_id": "BTCUSDT-PERP",
            "compile_hash": _DEMO_COMPILE_HASH,
            "compile_artifact_id": "art_demo_compiled_001",
            "validation_report_id": "vr_demo_compiled_001",
            "data_range": "2025-01-01:2025-06-01",
            **scope_payload,
        })
        # Leave it in CREATED stage — compile evidence present, replay missing
        result["demo_compiled"] = job_compiled.job_id

    # demo_replay_failed — a backtest job that failed
    detail_failed = repository.detail("demo_replay_failed")
    if detail_failed is not None:
        versions = detail_failed.get("versions", [])
        if versions:
            failed_version_id = versions[-1].get("strategy_version_id", "")  # type: ignore[union-attr]
            if failed_version_id:
                job_failed = backtest_service.create_job({
                    "strategy_spec_version_id": failed_version_id,
                    "adapter_profile_id": "BINANCE_PERP",
                    "instrument_id": "BTCUSDT-PERP",
                    "compile_hash": _DEMO_COMPILE_HASH_REPLAY,
                    "compile_artifact_id": "art_demo_failed_001",
                    "validation_report_id": "vr_demo_failed_001",
                    "data_range": "2025-01-01:2025-06-01",
                    **scope_payload,
                })
                backtest_service.transition_job(
                    job_failed.job_id,
                    "FAILED",
                )
                result["demo_replay_failed"] = job_failed.job_id

    # demo_replay_passed — a backtest job that succeeded with report artifacts
    detail_passed = repository.detail("demo_replay_passed")
    if detail_passed is not None:
        versions = detail_passed.get("versions", [])
        if versions:
            passed_version_id = versions[-1].get("strategy_version_id", "")  # type: ignore[union-attr]
            if passed_version_id:
                job_passed = backtest_service.create_job({
                    "strategy_spec_version_id": passed_version_id,
                    "adapter_profile_id": "BINANCE_PERP",
                    "instrument_id": "BTCUSDT-PERP",
                    "compile_hash": _DEMO_COMPILE_HASH_REPLAY,
                    "compile_artifact_id": "art_demo_passed_001",
                    "validation_report_id": "vr_demo_passed_001",
                    "data_range": "2025-01-01:2025-06-01",
                    **scope_payload,
                })
                backtest_service.transition_job(
                    job_passed.job_id,
                    "SUCCEEDED",
                    result_artifact_refs={
                        "report": f"reports/{_DEMO_REPORT_HASH}/backtest_report.html",
                        "trades": f"reports/{_DEMO_REPORT_HASH}/trades.json",
                        "fills": f"reports/{_DEMO_REPORT_HASH}/fills.json",
                    },
                )
                result["demo_replay_passed"] = job_passed.job_id

    # demo_promotion_requested — replay_passed + promotion state in strategy status
    detail_promo = repository.detail("demo_promotion_requested")
    if detail_promo is not None:
        versions = detail_promo.get("versions", [])
        if versions:
            promo_version_id = versions[-1].get("strategy_version_id", "")  # type: ignore[union-attr]
            if promo_version_id:
                job_promo = backtest_service.create_job({
                    "strategy_spec_version_id": promo_version_id,
                    "adapter_profile_id": "BINANCE_PERP",
                    "instrument_id": "BTCUSDT-PERP",
                    "compile_hash": _DEMO_COMPILE_HASH_REPLAY,
                    "compile_artifact_id": "art_demo_promo_req_001",
                    "validation_report_id": "vr_demo_promo_req_001",
                    "data_range": "2025-01-01:2025-06-01",
                    **scope_payload,
                })
                backtest_service.transition_job(
                    job_promo.job_id,
                    "SUCCEEDED",
                    result_artifact_refs={
                        "report": f"reports/{_DEMO_REPORT_HASH}/backtest_report.html",
                        "trades": f"reports/{_DEMO_REPORT_HASH}/trades.json",
                        "fills": f"reports/{_DEMO_REPORT_HASH}/fills.json",
                    },
                )
                result["demo_promotion_requested"] = job_promo.job_id

    # demo_promotion_ready — replay_passed + execution_ready status
    detail_ready = repository.detail("demo_promotion_ready")
    if detail_ready is not None:
        versions = detail_ready.get("versions", [])
        if versions:
            ready_version_id = versions[-1].get("strategy_version_id", "")  # type: ignore[union-attr]
            if ready_version_id:
                job_ready = backtest_service.create_job({
                    "strategy_spec_version_id": ready_version_id,
                    "adapter_profile_id": "BINANCE_PERP",
                    "instrument_id": "BTCUSDT-PERP",
                    "compile_hash": _DEMO_COMPILE_HASH_REPLAY,
                    "compile_artifact_id": "art_demo_promo_ready_001",
                    "validation_report_id": "vr_demo_promo_ready_001",
                    "data_range": "2025-01-01:2025-06-01",
                    **scope_payload,
                })
                backtest_service.transition_job(
                    job_ready.job_id,
                    "SUCCEEDED",
                    result_artifact_refs={
                        "report": f"reports/{_DEMO_REPORT_HASH}/backtest_report.html",
                        "trades": f"reports/{_DEMO_REPORT_HASH}/trades.json",
                        "fills": f"reports/{_DEMO_REPORT_HASH}/fills.json",
                    },
                )
                result["demo_promotion_ready"] = job_ready.job_id

    return result


def _scope_payload(context: UserProjectContext | None) -> dict[str, str]:
    if context is None:
        return {}
    return {"user_id": context.user_id, "project_id": context.project_id}


def main() -> int:
    """CLI entrypoint. Seeds demo strategies and evidence into in-memory stores.

    Note: Because the demo stores are in-memory by default, this script is
    primarily useful for integration test harnesses and the dev-server demo
    bootstrap (which calls seed_demo_strategies + seed_demo_evidence from
    services/api/fastapi_app.py when BUILDER_SEED_DEMO_STRATEGIES=1).

    For the live demo, prefer running the FastAPI server with
    BUILDER_SEED_DEMO_STRATEGIES=1 — the server bootstraps the demo data on
    startup.

    Exit code 0 on success, non-zero on error.
    """
    repository = InMemoryStrategyRepository()
    backtest_service = BacktestJobService()

    result = seed_demo_evidence(repository, backtest_service)

    print("Seeded demo strategies and evidence:")
    print(f"  repository: {len(repository._records)} strategies")  # noqa: SLF001
    print(f"  backtest jobs: {len(backtest_service._jobs_by_id)} jobs")  # type: ignore[attr-defined]  # noqa: SLF001
    for strategy_id, job_id in result.items():
        print(f"  {strategy_id}: {job_id or '(no job)'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
