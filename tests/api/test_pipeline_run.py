"""Tests for POST /api/pipeline/run endpoint (Web UI pipeline flow)."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

DUAL_MA_SPEC = (
    Path(__file__).resolve().parent.parent.parent
    / "docs" / "examples" / "specs" / "dual_ma.json"
)


class TestPipelineRunPayload:
    """Verify the pipeline run route handler works."""

    def test_pipeline_run_module_exists(self):
        from services.api.routes import pipeline_run
        assert hasattr(pipeline_run, "pipeline_run_payload")

    def test_pipeline_run_with_valid_spec(self):
        from services.api.routes.pipeline_run import pipeline_run_payload
        from services.api.router import ApiResponse

        spec = json.loads(DUAL_MA_SPEC.read_text())
        result = pipeline_run_payload(spec)
        assert isinstance(result, ApiResponse)
        assert result.status_code == 200

    def test_pipeline_run_result_is_valid(self):
        from services.api.routes.pipeline_run import pipeline_run_payload

        spec = json.loads(DUAL_MA_SPEC.read_text())
        result = pipeline_run_payload(spec)
        data = result.json()
        assert data.get("is_valid") is True

    def test_pipeline_run_shows_compilation(self):
        from services.api.routes.pipeline_run import pipeline_run_payload

        spec = json.loads(DUAL_MA_SPEC.read_text())
        result = pipeline_run_payload(spec)
        data = result.json()
        assert "compile_profile" in data
        assert data.get("execution_authority") is False

    def test_pipeline_run_shows_backtest_result(self):
        from services.api.routes.pipeline_run import pipeline_run_payload

        spec = json.loads(DUAL_MA_SPEC.read_text())
        result = pipeline_run_payload(spec)
        data = result.json()
        assert "summary_metrics" in data
        assert "total_trades" in data

    def test_pipeline_run_invalid_spec_fails(self):
        from services.api.routes.pipeline_run import pipeline_run_payload

        bad_spec = {"schema_version": "1.0"}  # Missing required fields
        result = pipeline_run_payload(bad_spec)
        assert result.status_code == 422

    def test_pipeline_run_forbidden_refs_fails(self):
        from services.api.routes.pipeline_run import pipeline_run_payload

        spec = json.loads(DUAL_MA_SPEC.read_text())
        spec["rules"]["evil"] = {"all": [{"eq": ["submit_order", "true"]}]}
        result = pipeline_run_payload(spec)
        assert result.status_code == 422
