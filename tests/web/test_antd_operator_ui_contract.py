from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
WEB = ROOT / "apps" / "web"


def test_web_manifest_declares_ant_design_react_stack_without_vue_migration() -> None:
    package = json.loads((WEB / "package.json").read_text())

    assert package["dependencies"]["antd"]
    assert package["dependencies"]["@ant-design/icons"]
    assert "vue" not in package.get("dependencies", {})
    assert "@ant-design-vue/pro-layout" not in package.get("dependencies", {})


def test_root_layout_mounts_builder_shell_with_ant_design() -> None:
    layout = (WEB / "app" / "layout.tsx").read_text()
    sidebar = (WEB / "components" / "shell" / "BuilderSidebar.tsx").read_text()
    banner = (WEB / "components" / "shell" / "BuilderSafetyBanner.tsx").read_text()

    assert 'import "antd/dist/reset.css"' in layout
    assert "BuilderShell" in layout
    assert "BuilderThemeProvider" in layout
    assert "Nautilus Builder" in sidebar
    assert "Builder-only mode" in banner
    assert "does not submit live orders" in banner
    for href in ("/", "/strategies", "/config", "/?tab=backtest", "/?tab=execution", "/results"):
        assert href in sidebar
    assert "submit_order" not in sidebar
    assert "TradeAction" not in sidebar


def test_home_page_uses_ant_design_dashboard_workflow_surface() -> None:
    page = (WEB / "app" / "page.tsx").read_text()
    dashboard = (WEB / "components" / "dashboard" / "BuilderDashboard.tsx").read_text()

    assert "BuilderDashboard" in page
    assert "DashboardCard" in dashboard
    for label in ("Strategy Builder", "Backtest Center", "Execution Lane"):
        assert label in dashboard
    assert "AiStrategyCopilot" in dashboard
    assert "PromotionRequestPanel" in dashboard
    assert "ExecutionLaneFeaturePanel" in dashboard
    assert "submit_order" not in page
    assert "TradeAction" not in page


def test_config_ui_uses_ant_design_form_tabs_without_browser_secrets() -> None:
    component = (WEB / "components" / "config" / "ModelConfigTabs.tsx").read_text()

    for token in ("Tabs", "Form", "Select", "Input", "Alert", "Badge"):
        assert token in component
    assert "OPENAI_API_KEY stays server-side only" in component
    assert "validate_strategy_spec() is mandatory" in component
    assert "submit_order / TradeAction blocked" in component
    assert 'type="password"' not in component
    assert 'name="apiKey"' not in component
    assert "secret_key" not in component.lower()
