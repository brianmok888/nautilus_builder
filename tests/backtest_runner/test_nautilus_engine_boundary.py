from __future__ import annotations

from packages.backtest_runner.nautilus_engine import NautilusBacktestEngineBoundary


def test_nautilus_engine_boundary_invokes_injected_engine_without_live_credentials() -> None:
    calls: list[dict[str, object]] = []

    class Engine:
        def run(self, config: dict[str, object]) -> dict[str, object]:
            calls.append(config)
            return {
                "equity_curve": [10000.0, 10001.0],
                "trades": [],
                "fills": [],
                "logs": ["nautilus fixture completed"],
            }

    boundary = NautilusBacktestEngineBoundary(engine=Engine())
    result = boundary.run(
        backtest_job_id="bt_001",
        strategy_spec_version="0.1.0-draft.1",
        adapter_id="BINANCE_PERP",
        instrument_id="BTCUSDT-PERP",
        compile_hash="abc123",
        validation_report_id="vr_001",
        worker_image="nautilus-builder-worker:dev",
    )

    assert calls[0]["adapter_id"] == "BINANCE_PERP"
    assert "credentials" not in calls[0]
    assert result.backtest_job_id == "bt_001"
    assert result.logs == ["nautilus fixture completed"]
