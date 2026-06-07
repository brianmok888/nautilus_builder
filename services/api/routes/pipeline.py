from __future__ import annotations

from typing import Any

from packages.pipeline.service import run_pipeline as _run_pipeline, request_pipeline_promotion as _request_promotion
from services.api.router import ApiResponse


def run_pipeline_payload(payload: dict[str, Any]) -> ApiResponse:
    result = _run_pipeline(payload)
    status_code = 200 if result.success else 422
    return ApiResponse(
        payload=result.model_dump(mode="json"),
        status_code=status_code,
    )


def promote_pipeline_payload(payload: dict[str, Any]) -> ApiResponse:
    strategy_version = str(payload.get("strategy_version", ""))
    compile_hash = str(payload.get("compile_hash", ""))
    target = str(payload.get("target", "shadow"))
    evidence_refs = payload.get("evidence_refs")

    if not strategy_version or not compile_hash:
        return ApiResponse(
            payload={"error": "missing_required_fields", "details": ["strategy_version", "compile_hash"]},
            status_code=422,
        )

    if not isinstance(evidence_refs, dict) or not evidence_refs:
        return ApiResponse(
            payload={"error": "promotion_evidence_missing", "details": ["evidence_refs"]},
            status_code=422,
        )

    from packages.pipeline.service import PipelineResult
    from packages.strategy_compiler.artifacts import CompileArtifact
    synthetic_artifact = CompileArtifact(
        profile="signal_preview_only",
        strategy_class="pipeline",
        output_mode="observational",
        execution_authority=False,
        spec_version=strategy_version,
        adapter_id="pipeline",
        instrument_id="pipeline",
        compile_hash=compile_hash,
    )
    synthetic_result = PipelineResult(
        success=True,
        compile_artifact=synthetic_artifact,
        promotion_evidence=evidence_refs,
        promotion_status="pending_approval",
    )
    gate_result = _request_promotion(pipeline_result=synthetic_result, target=target)

    status_code = 200 if gate_result.success else 422
    return ApiResponse(
        payload=gate_result.model_dump(mode="json"),
        status_code=status_code,
    )
