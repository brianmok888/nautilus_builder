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
    assert "Strategy Builder → Backtest Center → Execution Lane" in spec
    assert "1. Strategy Builder" in spec
    assert "2. Backtest Center" in spec
    assert "3. Execution Lane" in spec
    assert "Observational runtime console" in spec
    assert "/results/res_001" in spec
    assert "Backtest results" in spec
    assert "/strategies" in spec
    assert "/backtests/bt_job_001" in spec
    assert "Apply to Builder" in spec
    assert "Manual promotion before paper/live" in spec
    assert "Execution lane feature flags are backend-owned" in spec


def test_frontend_operator_mvp_verification_report_mentions_full_path_and_safety() -> None:
    report = (ROOT / "docs" / "verification" / "2026-05-23-frontend-operator-mvp-verification-report.md").read_text()

    assert "Strategy CRUD" in report
    assert "profile validation" in report
    assert "backtest job console" in report
    assert "AI draft" in report
    assert "safe promotion" in report
    assert "no live order authority" in report
