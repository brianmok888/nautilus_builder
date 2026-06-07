from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def test_frontend_package_manifest_declares_next_app_shell_scripts() -> None:
    package_json = ROOT / "apps" / "web" / "package.json"

    manifest = json.loads(package_json.read_text())

    assert manifest["scripts"]["dev"] == "next dev"
    assert manifest["scripts"]["build"] == "next build"
    assert manifest["dependencies"]["next"]
    assert manifest["dependencies"]["react"]


def test_next_app_shell_mounts_ant_design_operator_shell_without_runtime_authority() -> None:
    page = (ROOT / "apps" / "web" / "app" / "page.tsx").read_text()
    layout = (ROOT / "apps" / "web" / "app" / "layout.tsx").read_text()
    shell = (ROOT / "apps" / "web" / "components" / "shell" / "OperatorAppShell.tsx").read_text()
    dashboard = (ROOT / "apps" / "web" / "components" / "dashboard" / "BuilderDashboard.tsx").read_text()

    assert "BuilderDashboard" in page
    assert "OperatorAppShell" in layout
    assert "antd/dist/reset.css" in layout
    assert "Layout.Sider" in shell
    assert "JobTerminal" in dashboard
    assert "AiStrategyCopilot" in dashboard
    assert "Builder-only" in shell
    assert "No live order authority" in shell
    assert "submit_order" not in page
    assert "TradeAction" not in page
    assert "Nautilus Builder" in layout


def test_next_app_shell_imports_global_operator_styles() -> None:
    layout = (ROOT / "apps" / "web" / "app" / "layout.tsx").read_text()
    css = ROOT / "apps" / "web" / "app" / "globals.css"

    assert 'import "./globals.css"' in layout
    assert css.exists()
    css_text = css.read_text()
    for token in ("--nb-bg", ".nb-sidebar", ".operator-shell", ".operator-sider", ".builder-dashboard", ".terminal-line"):
        assert token in css_text, f"Expected CSS token {token!r} not found in globals.css"


def test_home_page_uses_visual_shell_without_live_authority() -> None:
    page = (ROOT / "apps" / "web" / "app" / "page.tsx").read_text()
    dashboard = (ROOT / "apps" / "web" / "components" / "dashboard" / "BuilderDashboard.tsx").read_text()

    assert "BuilderDashboard" in page
    assert "DashboardCard" in dashboard
    assert "submit_order" not in page
    assert "TradeAction" not in page
