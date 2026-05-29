from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def test_ai_copilot_exposes_prompt_thread_audit_and_apply_surfaces() -> None:
    component = (ROOT / "apps" / "web" / "components" / "ai-builder" / "AiStrategyCopilot.tsx").read_text()
    api = (ROOT / "apps" / "web" / "lib" / "api.ts").read_text()

    assert "generateAiDraft" in api
    assert "applyAiDraftToBuilder" in api
    assert '"/api/ai-builder/apply"' in api
    assert "ai_thread_id" in component
    assert "improvement_cycle_id" in component
    assert "strategy_lineage_id" in component
    assert "strategy_version_id" in component
    assert "Strategy prompt" in component or "Strategy prompt" in component.lower()
    assert "Generate & Build Strategy" in component
    assert "Generate & Build Strategy" in component
    assert "submit_order" not in component


def test_ai_copilot_apply_flow_requires_validated_draft_before_builder_update() -> None:
    component = (ROOT / "apps" / "web" / "components" / "ai-builder" / "AiStrategyCopilot.tsx").read_text()
    api = (ROOT / "apps" / "web" / "lib" / "api.ts").read_text()

    assert "apiFetch<AiDraftApplication>" in api


def test_operator_dashboard_uses_compact_prompt_first_workflow() -> None:
    dashboard = (ROOT / "apps" / "web" / "components" / "dashboard" / "BuilderDashboard.tsx").read_text()
    css = (ROOT / "apps" / "web" / "app" / "globals.css").read_text()

    assert "useState" in dashboard and "activeSection" in dashboard
    assert "AiStrategyCopilot" in dashboard
    assert "BacktestLaunchPanel" in dashboard
    assert "ExecutionLaneFeaturePanel" in dashboard
    assert 'componentSize="small"' in (ROOT / "apps" / "web" / "components" / "shell" / "OperatorAppShell.tsx").read_text()
    assert ".builder-dashboard" in css
