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


def test_root_layout_mounts_ant_design_operator_shell() -> None:
    layout = (WEB / "app" / "layout.tsx").read_text()
    shell = (WEB / "components" / "shell" / "OperatorAppShell.tsx").read_text()

    assert 'import "antd/dist/reset.css"' in layout
    assert "OperatorAppShell" in layout
    assert "ConfigProvider" in shell
    assert "Layout.Sider" in shell
    assert "Menu" in shell
    assert "Advisory-only" in shell
    assert "No live order authority" in shell
    for href in ("/", "/strategies", "/config", "/backtests/bt_job_001", "/results/res_001"):
        assert href in shell
    assert "submit_order" not in shell
    assert "TradeAction" not in shell


def test_home_page_uses_ant_design_dashboard_workflow_surface() -> None:
    page = (WEB / "app" / "page.tsx").read_text()
    dashboard = (WEB / "components" / "dashboard" / "BuilderDashboard.tsx").read_text()

    assert "BuilderDashboard" in page
    assert "Card" in dashboard
    assert "Statistic" in dashboard
    assert "Steps" in dashboard
    assert "Tabs" in dashboard
    for label in ("Strategy Builder", "Backtest Center", "Execution Lane", "BacktestNode", "Manual promotion"):
        assert label in dashboard
    assert "AiStrategyCopilot" in dashboard
    assert "StrategyBuilderWorkspace" in dashboard
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
