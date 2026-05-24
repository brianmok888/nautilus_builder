from __future__ import annotations

import tomllib
from pathlib import Path

from packages.backtest_runner.nautilus_engine import NautilusBacktestEngineBoundary
from packages.backtest_runner.runner import run_backtest_fixture


ROOT = Path(__file__).resolve().parents[2]
EXPECTED_NAUTILUS_VERSION = "1.223.0"


def test_pyproject_pins_nautilus_trader_to_daedalus_runtime() -> None:
    pyproject = tomllib.loads((ROOT / "pyproject.toml").read_text())

    assert f"nautilus_trader=={EXPECTED_NAUTILUS_VERSION}" in pyproject["project"]["dependencies"]


def test_fixture_runner_result_is_labeled_fixture_not_real_engine() -> None:
    result = run_backtest_fixture(
        strategy_spec_version="0.1.0-draft.1",
        adapter_id="BINANCE_PERP",
        instrument_id="BTCUSDT-PERP",
        compile_hash="abc123",
        worker_image="nautilus-builder-worker:dev",
    )

    assert result.engine_mode == "fixture"
    assert result.nautilus_trader_version == EXPECTED_NAUTILUS_VERSION
    assert result.artifact_refs["evidence_mode"] == "fixture"


def test_injected_engine_boundary_is_labeled_separate_from_fixture() -> None:
    calls: list[dict[str, object]] = []

    class Engine:
        def run(self, config: dict[str, object]) -> dict[str, object]:
            calls.append(config)
            return {"equity_curve": [10000.0], "trades": [], "fills": [], "logs": ["injected engine completed"]}

    result = NautilusBacktestEngineBoundary(engine=Engine()).run(
        backtest_job_id="bt_001",
        strategy_spec_version="0.1.0-draft.1",
        adapter_id="BINANCE_PERP",
        instrument_id="BTCUSDT-PERP",
        compile_hash="abc123",
        validation_report_id="vr_001",
        worker_image="nautilus-builder-worker:dev",
    )

    assert calls[0]["engine_mode"] == "injected_engine"
    assert calls[0]["nautilus_trader_version"] == EXPECTED_NAUTILUS_VERSION
    assert result.engine_mode == "injected_engine"
    assert result.nautilus_trader_version == EXPECTED_NAUTILUS_VERSION
