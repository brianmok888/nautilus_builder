"""Pipeline service tests — validate → compile → create job → run → results.

TDD: these tests define the contract for the pipeline service before it exists.
"""
from __future__ import annotations

from packages.ai_builder.provider import AdvisoryDraftProvider
from packages.pipeline.service import run_pipeline, PipelineResult


def _valid_spec() -> dict[str, object]:
    """Produce a valid StrategySpec payload using the fixture draft provider."""
    return AdvisoryDraftProvider().draft_spec("EMA RSI crossover strategy")


class TestPipelineContract:
    """The pipeline must chain all seams and return a single result."""

    def test_valid_spec_produces_successful_pipeline_result(self) -> None:
        spec = _valid_spec()
        result = run_pipeline(spec)

        assert isinstance(result, PipelineResult)
        assert result.success is True
        assert result.validation_report is not None
        assert result.validation_report.is_valid is True
        assert result.compile_artifact is not None
        assert result.compile_artifact.compile_hash != ""
        assert result.backtest_job is not None
        assert result.backtest_result is not None
        assert result.backtest_result.get("summary_metrics", {}).get("trade_count") is not None

    def test_invalid_spec_fails_at_validation_without_proceeding(self) -> None:
        result = run_pipeline({"bad": "payload"})

        assert result.success is False
        assert result.validation_report is not None
        assert result.validation_report.is_valid is False
        assert len(result.validation_report.errors) > 0
        assert result.compile_artifact is None
        assert result.backtest_job is None
        assert result.backtest_result is None

    def test_pipeline_result_includes_step_tracking(self) -> None:
        spec = _valid_spec()
        result = run_pipeline(spec)

        assert result.steps is not None
        step_names = [s.name for s in result.steps]
        assert "validate" in step_names
        assert "compile" in step_names
        assert "create_job" in step_names
        assert "run_backtest" in step_names

        for step in result.steps:
            assert step.status in ("succeeded", "failed", "skipped")

    def test_failed_step_skips_remaining(self) -> None:
        result = run_pipeline({"bad": "payload"})

        step_statuses = {s.name: s.status for s in result.steps}
        assert step_statuses["validate"] == "failed"
        assert step_statuses["compile"] == "skipped"
        assert step_statuses["create_job"] == "skipped"
        assert step_statuses["run_backtest"] == "skipped"

    def test_pipeline_result_is_json_serializable(self) -> None:
        spec = _valid_spec()
        result = run_pipeline(spec)

        serialized = result.model_dump(mode="json")
        assert isinstance(serialized, dict)
        assert "success" in serialized
        assert "steps" in serialized

    def test_successful_pipeline_collects_promotion_evidence(self) -> None:
        spec = _valid_spec()
        result = run_pipeline(spec)

        assert result.promotion_evidence is not None
        assert "validation_report" in result.promotion_evidence
        assert "backtest_result" in result.promotion_evidence
        assert result.promotion_evidence["validation_report"] != ""
        assert result.promotion_evidence["backtest_result"] != ""

    def test_pipeline_does_not_auto_promote(self) -> None:
        spec = _valid_spec()
        result = run_pipeline(spec)

        assert result.promotion_request is None
        assert result.promotion_status == "pending_approval"

    def test_request_promotion_after_successful_pipeline(self) -> None:
        spec = _valid_spec()
        result = run_pipeline(spec)

        from packages.pipeline.service import request_pipeline_promotion
        promotion_result = request_pipeline_promotion(
            pipeline_result=result,
            target="shadow",
        )

        assert promotion_result.success is True
        assert promotion_result.promotion_status == "manual_approval_pending"
        assert promotion_result.promotion_request is not None
        assert promotion_result.promotion_request.may_submit_order is False
        assert promotion_result.promotion_request.may_create_trade_action is False

    def test_cannot_promote_failed_pipeline(self) -> None:
        result = run_pipeline({"bad": "payload"})

        from packages.pipeline.service import request_pipeline_promotion
        promotion_result = request_pipeline_promotion(
            pipeline_result=result,
            target="shadow",
        )

        assert promotion_result.success is False
        assert promotion_result.promotion_status == "blocked"
