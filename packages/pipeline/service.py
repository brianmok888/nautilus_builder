from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict

from packages.backtest_jobs.service import BacktestJobService
from packages.backtest_runner.contracts import BacktestRunManifest
from packages.backtest_runner.result_normalizer import normalize_backtest_result
from packages.backtest_runner.runner import run_backtest_fixture
from packages.strategy_compiler.compiler import compile_strategy_spec
from packages.strategy_compiler.artifacts import CompileArtifact
from packages.strategy_validation.reports import ValidationReport
from packages.strategy_validation.validators import validate_strategy_spec
from packages.promotions.service import PromotionService
from packages.promotions.models import PromotionRequest


class PipelineStep(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    status: str


class PipelineResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    success: bool
    validation_report: ValidationReport | None = None
    compile_artifact: CompileArtifact | None = None
    backtest_job: dict[str, Any] | None = None
    backtest_result: dict[str, Any] | None = None
    steps: list[PipelineStep] = []
    promotion_evidence: dict[str, str] | None = None
    promotion_request: PromotionRequest | None = None
    promotion_status: str = "not_applicable"


class PromotionGateResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    success: bool
    promotion_status: str
    promotion_request: PromotionRequest | None = None
    error: str | None = None


def run_pipeline(spec_payload: dict[str, Any]) -> PipelineResult:
    steps: list[PipelineStep] = []

    validation_report = validate_strategy_spec(spec_payload)
    if not validation_report.is_valid:
        steps.append(PipelineStep(name="validate", status="failed"))
        steps.extend([
            PipelineStep(name="compile", status="skipped"),
            PipelineStep(name="create_job", status="skipped"),
            PipelineStep(name="run_backtest", status="skipped"),
        ])
        return PipelineResult(
            success=False,
            validation_report=validation_report,
            steps=steps,
        )

    steps.append(PipelineStep(name="validate", status="succeeded"))

    try:
        compile_artifact = compile_strategy_spec(spec_payload, profile="backtest")
    except Exception:
        steps.append(PipelineStep(name="compile", status="failed"))
        steps.extend([
            PipelineStep(name="create_job", status="skipped"),
            PipelineStep(name="run_backtest", status="skipped"),
        ])
        return PipelineResult(
            success=False,
            validation_report=validation_report,
            steps=steps,
        )

    steps.append(PipelineStep(name="compile", status="succeeded"))

    job_service = BacktestJobService()
    job_payload: dict[str, str] = {
        "strategy_spec_version_id": compile_artifact.spec_version,
        "adapter_profile_id": compile_artifact.adapter_id,
        "instrument_id": compile_artifact.instrument_id,
        "compile_hash": compile_artifact.compile_hash,
        "validation_report_id": "vr_pipeline_auto",
        "data_range": spec_payload.get("data_range", {}).get("start", "") + ":" + spec_payload.get("data_range", {}).get("end", "") if isinstance(spec_payload.get("data_range"), dict) else "unspecified",
        "dataset_id": "pipeline_fixture",
        "data_type": "historical_bars",
        "timeframe": "1m",
        "market_type": "crypto_perp",
    }
    job = job_service.create_job(job_payload)
    steps.append(PipelineStep(name="create_job", status="succeeded"))

    result_artifact = run_backtest_fixture(
        backtest_job_id=job.job_id,
        strategy_spec_version=compile_artifact.spec_version,
        adapter_id=compile_artifact.adapter_id,
        instrument_id=compile_artifact.instrument_id,
        compile_hash=compile_artifact.compile_hash,
        worker_image="nautilus-builder-worker:latest",
    )
    steps.append(PipelineStep(name="run_backtest", status="succeeded"))

    return PipelineResult(
        success=True,
        validation_report=validation_report,
        compile_artifact=compile_artifact,
        backtest_job=job.model_dump(mode="json"),
        backtest_result=result_artifact.model_dump(mode="json"),
        steps=steps,
        promotion_evidence={
            "validation_report": f"vr_pipeline_auto:{compile_artifact.compile_hash}",
            "backtest_result": f"br:{job.job_id}:{compile_artifact.compile_hash}",
            "no_lookahead_report": "not_applicable:pipeline_fixture",
            "gate_compatibility_report": "gate:compatible:pipeline",
            "runtime_boundary_report": "runtime:observational_only",
            "risk_review": "pending",
        },
        promotion_status="pending_approval",
    )


def request_pipeline_promotion(
    *,
    pipeline_result: PipelineResult,
    target: str,
) -> PromotionGateResult:
    if not pipeline_result.success:
        return PromotionGateResult(
            success=False,
            promotion_status="blocked",
            error="pipeline_failed_cannot_promote",
        )

    if not pipeline_result.promotion_evidence:
        return PromotionGateResult(
            success=False,
            promotion_status="blocked",
            error="no_promotion_evidence",
        )

    if not pipeline_result.compile_artifact:
        return PromotionGateResult(
            success=False,
            promotion_status="blocked",
            error="no_compile_artifact",
        )

    promotion = PromotionService().request_builder_promotion(
        strategy_version_id=pipeline_result.compile_artifact.spec_version,
        result_id=pipeline_result.promotion_evidence["backtest_result"],
        target=target,
    )

    return PromotionGateResult(
        success=True,
        promotion_status=str(promotion.get("approval_state", "unknown")),
        promotion_request=PromotionRequest(
            strategy_version=pipeline_result.compile_artifact.spec_version,
            compile_hash=pipeline_result.compile_artifact.compile_hash,
            profile="signal_preview_only",
            may_submit_order=False,
            may_create_trade_action=False,
            gate_compatibility=True,
            manual_approval=True,
            evidence_refs=pipeline_result.promotion_evidence,
        ),
    )
