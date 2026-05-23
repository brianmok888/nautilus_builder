from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def test_results_dashboard_exposes_observational_tabs_and_api_contracts() -> None:
    dashboard = (ROOT / "apps" / "web" / "components" / "results" / "ResultsDashboard.tsx").read_text()
    api = (ROOT / "apps" / "web" / "lib" / "api.ts").read_text()

    for label in ("Summary", "Equity", "Trades", "Fills", "Logs", "Artifacts"):
        assert label in dashboard
    assert "fetchResultSummary" in api
    assert "fetchResultArtifacts" in api
    assert "fetchResultTrades" in api
    assert "fetchResultFills" in api
    assert "submit_order" not in dashboard
    assert "TradeAction" not in dashboard


def test_result_route_uses_dashboard_and_backend_result_id() -> None:
    page = (ROOT / "apps" / "web" / "app" / "results" / "[resultId]" / "page.tsx").read_text()

    assert "ResultsDashboard" in page
    assert "resultId" in page
