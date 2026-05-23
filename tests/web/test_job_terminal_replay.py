from __future__ import annotations

from packages.ui_contracts.job_terminal import ALLOWED_TERMINAL_COMMANDS, run_terminal_command


def test_reconnect_replay_works() -> None:
    replay = run_terminal_command("replay")

    assert replay["mode"] == "observational"
    assert replay["action"] == "replay"


def test_allowed_commands_only() -> None:
    assert set(ALLOWED_TERMINAL_COMMANDS) == {"status", "help", "metrics", "validation", "replay", "cancel"}


def test_request_cancel_maps_to_backend_durable_state() -> None:
    response = run_terminal_command("cancel")

    assert response["action"] == "cancel_request"
    assert response["backend_owned"] is True


def test_metrics_command_returns_observational_dashboard_link() -> None:
    response = run_terminal_command("metrics", job_id="job_001", result_id="res_001")

    assert response["mode"] == "observational"
    assert response["result_id"] == "res_001"
    assert response["dashboard_path"] == "/results/res_001"
