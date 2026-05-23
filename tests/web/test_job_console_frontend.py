from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def test_job_terminal_declares_allowed_commands_and_forbidden_shell_boundary() -> None:
    parser = (ROOT / "apps" / "web" / "components" / "terminal" / "commands.ts").read_text()
    terminal = (ROOT / "apps" / "web" / "components" / "terminal" / "JobTerminal.tsx").read_text()

    assert "ALLOWED_TERMINAL_COMMANDS" in parser
    assert "request cancel" in parser
    assert "bash" in parser
    assert "forbidden" in parser
    assert "parseTerminalCommand" in terminal
    assert "observational" in terminal


def test_backtest_job_frontend_page_uses_status_events_and_cancel_contracts() -> None:
    page = (ROOT / "apps" / "web" / "app" / "backtests" / "[jobId]" / "page.tsx").read_text()
    api = (ROOT / "apps" / "web" / "lib" / "api.ts").read_text()

    assert "fetchBacktestJob" in api
    assert "cancelBacktestJob" in api
    assert "fetchBacktestJobEvents" in api
    assert "Observational runtime console" in page
    assert "request cancel" in page
