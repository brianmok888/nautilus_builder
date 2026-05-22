from __future__ import annotations

import pytest

from packages.backtest_runner.config_builder import build_backtest_config


def test_config_builder_rejects_live_credentials() -> None:
    with pytest.raises(ValueError, match="live credentials"):
        build_backtest_config(
            strategy_spec_version="0.1.0-draft.1",
            adapter_id="BINANCE_PERP",
            instrument_id="BTCUSDT-PERP",
            compile_hash="abc123",
            validation_report_id="vr_001",
            worker_image="nautilus-builder-worker:dev",
            credentials={"api_key": "secret"},
        )
