from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def test_playwright_configuration_targets_next_shell_and_results_route() -> None:
    config = (ROOT / "apps" / "web" / "playwright.config.ts").read_text()

    assert "baseURL: \"http://127.0.0.1:3000\"" in config
    assert "next dev" in config
    assert "webServer" in config


def test_browser_e2e_spec_checks_builder_shell_and_results_dashboard() -> None:
    spec = (ROOT / "apps" / "web" / "e2e" / "builder-shell.spec.ts").read_text()

    assert "Nautilus Builder" in spec
    assert "Strategy draft authoring" in spec
    assert "Observational runtime console" in spec
    assert "/results/res_001" in spec
    assert "Backtest results" in spec
