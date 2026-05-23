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
    assert "backend validation" in component
    assert "submit_order" not in component
