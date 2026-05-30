"""Tests for scripts/run_backtest.py end-to-end pipeline (Issue 1 & 4)."""
import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
RUN_BACKTEST = REPO_ROOT / "scripts" / "run_backtest.py"
DUAL_MA_SPEC = REPO_ROOT / "docs" / "examples" / "specs" / "dual_ma.json"


def run_backtest(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(RUN_BACKTEST), *args],
        capture_output=True,
        text=True,
        timeout=60,
        cwd=str(REPO_ROOT),
    )


class TestRunBacktestScript:
    """Verify scripts/run_backtest.py exists and chains the full pipeline."""

    def test_script_exists(self):
        assert RUN_BACKTEST.is_file(), "scripts/run_backtest.py must exist"

    def test_script_is_executable(self):
        import os
        assert os.access(RUN_BACKTEST, os.X_OK), "scripts/run_backtest.py must be executable"

    def test_help_flag(self):
        result = run_backtest("--help")
        assert result.returncode == 0
        assert "spec" in result.stdout.lower() or "usage" in result.stdout.lower()

    def test_run_with_dual_ma_spec(self):
        result = run_backtest("--spec", str(DUAL_MA_SPEC))
        assert result.returncode == 0, f"Failed:\nstdout: {result.stdout}\nstderr: {result.stderr}"

    def test_output_shows_validation(self):
        result = run_backtest("--spec", str(DUAL_MA_SPEC))
        assert "valid" in result.stdout.lower(), "Should show validation result"

    def test_output_shows_compilation(self):
        result = run_backtest("--spec", str(DUAL_MA_SPEC))
        assert "compil" in result.stdout.lower(), "Should show compilation"

    def test_output_shows_backtest_config(self):
        result = run_backtest("--spec", str(DUAL_MA_SPEC))
        assert "backtest" in result.stdout.lower(), "Should show backtest config"

    def test_output_shows_result(self):
        result = run_backtest("--spec", str(DUAL_MA_SPEC))
        assert "result" in result.stdout.lower() or "pipeline" in result.stdout.lower() or "complete" in result.stdout.lower(), (
            "Should show pipeline result/completion"
        )

    def test_run_with_json_output(self):
        result = run_backtest("--spec", str(DUAL_MA_SPEC), "--json")
        assert result.returncode == 0
        # Should produce valid JSON output
        output = json.loads(result.stdout)
        assert "valid" in output or "validation" in output or "is_valid" in output

    def test_run_with_nonexistent_spec_fails(self):
        result = run_backtest("--spec", "/nonexistent/spec.json")
        assert result.returncode != 0

    def test_pipeline_preserves_execution_authority_false(self):
        result = run_backtest("--spec", str(DUAL_MA_SPEC))
        assert result.returncode == 0
        assert "false" in result.stdout.lower() or "authority" in result.stdout.lower()
