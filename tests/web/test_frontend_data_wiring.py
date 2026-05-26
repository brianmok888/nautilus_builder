from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def test_frontend_api_client_declares_market_and_strategy_fetches() -> None:
    client = (ROOT / "apps" / "web" / "lib" / "api.ts").read_text()

    assert "fetchAdapters" in client
    assert "fetchStrategies" in client
    assert "validateBacktestProfile" in client
    assert "/api/adapters" in client
    assert "/api/strategies" in client


def test_strategy_builder_page_mounts_market_selection_and_spec_editor_surfaces() -> None:
    component = (ROOT / "apps" / "web" / "components" / "strategy-builder" / "StrategyBuilderWorkspace.tsx").read_text()

    assert "MarketSelectionPanel" in component
    assert "StrategySpecEditor" in component
    assert "fetchAdapters" in component
    assert "validateBacktestProfile" in component
    assert "backend validation" in component
    assert "submit_order" not in component


def test_strategy_pages_expose_list_detail_and_builder_entrypoints() -> None:
    list_page = (ROOT / "apps" / "web" / "app" / "strategies" / "page.tsx").read_text()
    detail_page = (ROOT / "apps" / "web" / "app" / "strategies" / "[strategyId]" / "page.tsx").read_text()
    list_client = (ROOT / "apps" / "web" / "components" / "strategies" / "StrategyListClient.tsx").read_text()
    detail_client = (ROOT / "apps" / "web" / "components" / "strategies" / "StrategyDetailClient.tsx").read_text()

    assert "StrategyListClient" in list_page
    assert "fetchStrategies" in list_client
    assert "Strategy list" in list_page
    assert "StrategyDetailClient" in detail_page
    assert "Version history" in detail_client
    assert "Open in Builder" in detail_client
    assert "strategy_lineage_id" in detail_client


def test_frontend_api_client_declares_backtestnode_run_trigger() -> None:
    client = (ROOT / "apps" / "web" / "lib" / "api.ts").read_text()
    launch_panel = (ROOT / "apps" / "web" / "components" / "backtests" / "BacktestLaunchPanel.tsx").read_text()

    assert "runBacktestJob" in client
    assert "/api/backtest-jobs/${jobId}/run" in client
    assert "Run BacktestNode" in launch_panel
    assert "backend_owned_backtestnode" in launch_panel
    assert "Submit order" not in launch_panel
