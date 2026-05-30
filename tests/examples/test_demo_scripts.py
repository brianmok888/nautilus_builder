"""Tests for runnable demo scripts in docs/examples/ (S14)."""
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
EXAMPLES_DIR = REPO_ROOT / "docs" / "examples"


def run_script(script_name: str) -> subprocess.CompletedProcess:
    """Run an example script and return the result."""
    script = EXAMPLES_DIR / script_name
    return subprocess.run(
        [sys.executable, str(script)],
        capture_output=True,
        text=True,
        timeout=30,
        cwd=str(REPO_ROOT),
    )


class TestDemoStrategyBasic:
    """Verify demo_strategy_basic.py runs successfully."""

    def test_basic_script_exists(self):
        script = EXAMPLES_DIR / "demo_strategy_basic.py"
        assert script.is_file(), "docs/examples/demo_strategy_basic.py must exist"

    def test_basic_script_runs(self):
        result = run_script("demo_strategy_basic.py")
        assert result.returncode == 0, (
            f"demo_strategy_basic.py failed:\nstdout: {result.stdout}\nstderr: {result.stderr}"
        )

    def test_basic_script_outputs_strategy_id(self):
        result = run_script("demo_strategy_basic.py")
        assert "spec" in result.stdout.lower() or "strategy" in result.stdout.lower(), (
            "demo_strategy_basic.py should mention strategy/spec in output"
        )

    def test_basic_script_validates(self):
        result = run_script("demo_strategy_basic.py")
        assert "valid" in result.stdout.lower(), (
            "demo_strategy_basic.py should report validation status"
        )


class TestDemoStrategyBacktest:
    """Verify demo_strategy_backtest.py runs successfully."""

    def test_backtest_script_exists(self):
        script = EXAMPLES_DIR / "demo_strategy_backtest.py"
        assert script.is_file(), "docs/examples/demo_strategy_backtest.py must exist"

    def test_backtest_script_runs(self):
        result = run_script("demo_strategy_backtest.py")
        assert result.returncode == 0, (
            f"demo_strategy_backtest.py failed:\nstdout: {result.stdout}\nstderr: {result.stderr}"
        )

    def test_backtest_script_compiles(self):
        result = run_script("demo_strategy_backtest.py")
        assert "compile" in result.stdout.lower(), (
            "demo_strategy_backtest.py should show compilation"
        )

    def test_backtest_script_builds_config(self):
        result = run_script("demo_strategy_backtest.py")
        assert "backtest" in result.stdout.lower() or "config" in result.stdout.lower(), (
            "demo_strategy_backtest.py should show backtest config"
        )


class TestDemoAdapterDiscovery:
    """Verify demo_adapter_discovery.py runs successfully."""

    def test_adapter_script_exists(self):
        script = EXAMPLES_DIR / "demo_adapter_discovery.py"
        assert script.is_file(), "docs/examples/demo_adapter_discovery.py must exist"

    def test_adapter_script_runs(self):
        result = run_script("demo_adapter_discovery.py")
        assert result.returncode == 0, (
            f"demo_adapter_discovery.py failed:\nstdout: {result.stdout}\nstderr: {result.stderr}"
        )

    def test_adapter_script_lists_adapters(self):
        result = run_script("demo_adapter_discovery.py")
        assert "adapter" in result.stdout.lower(), (
            "demo_adapter_discovery.py should mention adapters"
        )
