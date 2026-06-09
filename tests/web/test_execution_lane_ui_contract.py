from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
WEB = ROOT / "apps" / "web"


def test_execution_page_exposes_execution_lane_venue_feature_panel() -> None:
    page = (WEB / "app" / "execution" / "page.tsx").read_text()
    dashboard = (WEB / "components" / "dashboard" / "BuilderDashboard.tsx").read_text()
    component = (WEB / "components" / "config" / "ExecutionLaneFeaturePanel.tsx").read_text()
    types = (WEB / "lib" / "types.ts").read_text()
    api = (WEB / "lib" / "api.ts").read_text()

    assert "BuilderDashboard" in page
    assert 'initialTab="execution"' in page
    assert "ExecutionLaneFeaturePanel" in dashboard
    assert "Execution lane venue binding" in component
    assert "Adapter ID" in component
    assert "Venue" in component
    assert "Execution lane UI" in component
    assert "Paper controls" in component
    assert "Live controls" in component
    assert "credential inputs allowed: false" in component
    assert "server-side credential slot only" in component
    config = (WEB / "app" / "config" / "page.tsx").read_text()
    assert "CredentialSlotBootstrap" not in config
    assert "Credential variable" not in component
    assert "Credential value" not in component
    assert "Input.Password" not in component
    assert "NEXT_PUBLIC" not in component
    assert "saveExecutionLaneCredentialSlot" not in api
    assert "/api/execution-lane/credential-slots" not in api
    assert "ExecutionLaneStatus" in types
    assert "ExecutionLaneProfile" in types
    assert "ExecutionLaneCommand" not in types
    assert "ExecutionLaneRuntimePlan" in types
    assert "ExecutionLaneSession" not in types
    assert "ExecutionLaneReport" not in types
    assert "fetchExecutionLaneStatus" in api
    assert "registerExecutionLaneProfile" in api
    assert "fetchExecutionLaneRuntimePlan" in api
    assert "order_intent" not in component
    assert "risk_decision" not in component
    assert "startExecutionLanePaperSession" not in api
    assert "stopExecutionLaneSession" not in api
    assert "/api/execution-lane/commands" not in api
    assert "/api/execution-lane/sessions/start" not in api
    assert "enqueueExecutionLaneCommand" not in api
    assert "runExecutionLaneWorkerOnce" not in api
    assert "Wire paper profile" in component
    assert "Queue paper command" not in component
    assert "Run backend worker plan" not in component
    assert "Runtime plan" in component
    assert "Worker report" not in component
    assert "paper sandbox only" in component
    assert "/api/execution-lane/worker/run-once" not in api
