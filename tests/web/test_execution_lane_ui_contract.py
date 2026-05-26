from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
WEB = ROOT / "apps" / "web"


def test_config_page_exposes_execution_lane_venue_feature_panel() -> None:
    page = (WEB / "app" / "config" / "page.tsx").read_text()
    component = (WEB / "components" / "config" / "ExecutionLaneFeaturePanel.tsx").read_text()
    types = (WEB / "lib" / "types.ts").read_text()
    api = (WEB / "lib" / "api.ts").read_text()

    assert "ExecutionLaneFeaturePanel" in page
    assert "Execution lane venue binding" in component
    assert "Adapter ID" in component
    assert "Venue" in component
    assert "Execution lane UI" in component
    assert "Paper controls" in component
    assert "Live controls" in component
    assert "credential inputs allowed: false" in component
    assert "server-side credential slot only" in component
    assert 'type="password"' not in component
    assert "api_key" not in component.lower()
    assert "ExecutionLaneStatus" in types
    assert "fetchExecutionLaneStatus" in api
