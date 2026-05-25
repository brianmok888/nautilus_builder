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


def test_next_app_shell_mounts_existing_placeholder_components_without_runtime_authority() -> None:
    page = (ROOT / "apps" / "web" / "app" / "page.tsx").read_text()
    layout = (ROOT / "apps" / "web" / "app" / "layout.tsx").read_text()

    assert "StrategyBuilderWorkspace" in page
    assert "JobTerminal" in page
    assert "AiStrategyCopilot" in page
    assert "draft authoring" in page
    assert "observational" in page
    assert "advisory" in page
    assert "submit_order" not in page
    assert "TradeAction" not in page
    assert "Nautilus Builder" in layout


def test_next_app_shell_imports_global_operator_styles() -> None:
    layout = (ROOT / "apps" / "web" / "app" / "layout.tsx").read_text()
    css = ROOT / "apps" / "web" / "app" / "globals.css"

    assert 'import "./globals.css"' in layout
    assert css.exists()
    css_text = css.read_text()
    for token in ("--builder-bg", ".app-shell", ".dashboard-grid", ".card", ".status-badge", ".terminal-card"):
        assert token in css_text


def test_home_page_uses_visual_shell_without_live_authority() -> None:
    page = (ROOT / "apps" / "web" / "app" / "page.tsx").read_text()

    for token in ("app-shell", "hero-card", "workflow-nav", "dashboard-grid", "card"):
        assert token in page
    assert "submit_order" not in page
    assert "TradeAction" not in page
