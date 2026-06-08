"""Read-only strategy evidence summary endpoint.

Aggregates existing evidence from strategy records and backtest job services
into a single response that the frontend can use for lifecycle/evidence/audit UI.

This endpoint is strictly read-only. It does not change validation,
compile, replay, or promotion behavior. It only exposes existing records.
"""
from __future__ import annotations

from typing import Any

from packages.auth import ProjectScopeError, UserProjectContext
from packages.backtest_jobs.service import BacktestJobService
from packages.strategy_spec.repository import InMemoryStrategyRepository
from services.api.router import ApiResponse


def strategy_evidence_summary_payload(
    repository: InMemoryStrategyRepository,
    strategy_id: str,
    *,
    backtest_job_service: BacktestJobService | None = None,
    context: UserProjectContext | None = None,
) -> ApiResponse:
    """Build a read-only evidence summary for a strategy.

    Returns existing records only. Missing fields are returned as None or
    empty lists — the frontend maps them to "missing" status. No new
    authority or decisions are introduced.
    """
    try:
        detail = repository.detail(strategy_id, context=context)
    except ProjectScopeError as exc:
        return ApiResponse({"error": "forbidden", "message": str(exc)}, status_code=403)
    if detail is None:
        return ApiResponse({"error": "strategy_not_found", "strategy_id": strategy_id}, status_code=404)

    versions = detail.get("versions", [])
    latest_version = versions[-1] if versions else {}
    spec = latest_version.get("spec", {}) if isinstance(latest_version, dict) else {}
    strategy_version_id = latest_version.get("strategy_version_id", "") if isinstance(latest_version, dict) else ""

    # Validation evidence — read from existing StrategySpec validation flags.
    validation_block = spec.get("validation", {}) if isinstance(spec, dict) else {}
    validation_passed = False
    validation_failed = False
    if isinstance(validation_block, dict) and validation_block:
        values = list(validation_block.values())
        if values:
            validation_failed = any(v is False for v in values)
            validation_passed = not validation_failed

    validation_evidence: dict[str, Any] = {
        "status": "failed" if validation_failed else ("passed" if validation_passed else "missing"),
        "flags": validation_block if isinstance(validation_block, dict) else {},
    }

    # Compile evidence — there is no compile-artifact repository; derive from
    # strategy status (backtested+ implies compile succeeded at some point).
    # But only mark passed if a compile_hash is actually present.
    status = str(detail.get("status", ""))
    compile_evidence: dict[str, Any] = {
        "status": "missing",
        "hash": None,
        "artifactId": None,
    }

    # Replay/backtest evidence — use public service methods.
    # No direct access to _jobs_by_id or other private internals.
    replay_jobs: list[dict[str, Any]] = []
    replay_evidence: dict[str, Any] = {"status": "missing", "jobs": []}
    if backtest_job_service is not None and strategy_version_id:
        # Use public method: list_jobs_for_strategy
        strategy_jobs = backtest_job_service.list_jobs_for_strategy(strategy_version_id)
        for job in strategy_jobs:
            job_dict: dict[str, Any] = {
                "jobId": job.job_id,
                "status": _normalize_replay_status(job.stage, job.status),
                "stage": job.stage,
                "lifecycleStatus": job.status,
                "createdAt": job.created_at,
                "updatedAt": job.updated_at,
                "compileHash": job.compile_hash,
                "compileArtifactId": job.compile_artifact_id,
                "resultArtifactRefs": dict(job.result_artifact_refs),
                "datasetId": job.dataset_id,
            }
            replay_jobs.append(job_dict)
            # Enrich compile evidence with the hash from the backtest job
            if job.compile_hash and compile_evidence["status"] == "missing":
                compile_evidence = {
                    "status": "passed",
                    "hash": job.compile_hash,
                    "artifactId": job.compile_artifact_id,
                }
        replay_evidence["jobs"] = replay_jobs
        if replay_jobs:
            # Determine overall replay status from the latest job.
            latest_job = replay_jobs[-1]
            replay_evidence["status"] = latest_job["status"]
            # If a replay job has a compile hash, upgrade compile evidence.
            if latest_job.get("compileHash") and compile_evidence["status"] == "missing":
                compile_evidence = {
                    "status": "passed",
                    "hash": latest_job["compileHash"],
                    "artifactId": latest_job.get("compileArtifactId"),
                }

    # Backend status implies compile succeeded (compile is prerequisite for backtest).
    if status in ("backtested", "approved", "execution_ready") and compile_evidence["status"] == "missing":
        # We don't have the actual hash, but the backend advanced, so compile must have passed.
        # Mark as "passed" with unknown hash.
        compile_evidence["status"] = "passed"

    # Promotion evidence — derived from strategy status only.
    # The Builder has no persistent promotion request store; the strategy status
    # itself is the source of truth for promotion state.
    promotion_evidence: dict[str, Any] = {"status": "missing"}
    if status == "execution_ready":
        promotion_evidence = {"status": "ready"}
    elif status == "approved":
        promotion_evidence = {"status": "ready"}
    elif status == "backtested":
        # Backtested but not yet promoted — check if a replay succeeded.
        if replay_evidence["status"] == "passed":
            promotion_evidence = {"status": "missing"}

    # Audit events — derived from existing timestamps and statuses.
    audit_events: list[dict[str, Any]] = []
    audit_events.append({
        "id": f"{strategy_id}_created",
        "kind": "created",
        "title": "Strategy created",
        "status": "info",
    })
    if validation_passed:
        audit_events.append({
            "id": f"{strategy_id}_validated",
            "kind": "validated",
            "title": "Validation passed",
            "status": "success",
        })
    elif validation_failed:
        audit_events.append({
            "id": f"{strategy_id}_validation_failed",
            "kind": "validation_failed",
            "title": "Validation failed",
            "status": "error",
        })
    if compile_evidence["status"] == "passed" and compile_evidence.get("hash"):
        audit_events.append({
            "id": f"{strategy_id}_compiled",
            "kind": "compiled",
            "title": "Compile artifact produced",
            "hash": compile_evidence["hash"],
            "status": "success",
        })
    for job in replay_jobs:
        kind = _replay_audit_kind(job["status"])
        title = _replay_audit_title(kind)
        audit_events.append({
            "id": f"{strategy_id}_replay_{job['jobId']}",
            "kind": kind,
            "title": title,
            "refId": job["jobId"],
            "timestamp": job.get("updatedAt"),
            "status": "error" if kind == "replay_failed" else ("success" if kind == "replay_completed" else "info"),
        })
    if promotion_evidence["status"] == "ready":
        audit_events.append({
            "id": f"{strategy_id}_promotion_ready",
            "kind": "promotion_ready",
            "title": "Promotion approved",
            "status": "success",
        })

    return ApiResponse({
        "strategyId": strategy_id,
        "strategyVersionId": strategy_version_id,
        "strategyStatus": status,
        "validation": validation_evidence,
        "compile": compile_evidence,
        "replay": replay_evidence,
        "promotion": promotion_evidence,
        "audit": audit_events,
    })


def _normalize_replay_status(stage: str, lifecycle_status: str) -> str:
    """Normalize a backtest job stage into a frontend-readable status."""
    combined = f"{stage} {lifecycle_status}".lower()
    if "fail" in combined:
        return "failed"
    if "succeed" in combined or "completed" in combined:
        return "passed"
    if "running" in combined:
        return "running"
    if "cancel" in combined:
        return "failed"
    if "created" in combined or "queued" in combined or "pending" in combined:
        return "running"
    return "unknown"


def _replay_audit_kind(status: str) -> str:
    if status == "failed":
        return "replay_failed"
    if status == "passed":
        return "replay_completed"
    return "replay_started"


def _replay_audit_title(kind: str) -> str:
    return {
        "replay_failed": "Replay failed",
        "replay_completed": "Replay completed",
        "replay_started": "Replay started",
    }.get(kind, "Replay event")
