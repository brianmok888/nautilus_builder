from __future__ import annotations


ALLOWED_TERMINAL_COMMANDS = ["status", "help", "metrics", "validation", "replay", "cancel"]


def run_terminal_command(
    command: str,
    *,
    job_id: str | None = None,
    result_id: str | None = None,
) -> dict[str, object]:
    if command not in ALLOWED_TERMINAL_COMMANDS:
        raise ValueError("command not allowed")

    if command == "cancel":
        return {
            "mode": "observational",
            "action": "cancel_request",
            "backend_owned": True,
        }

    if command == "metrics" and result_id is not None:
        return {
            "mode": "observational",
            "action": "metrics",
            "backend_owned": True,
            "job_id": job_id,
            "result_id": result_id,
            "dashboard_path": f"/results/{result_id}",
        }

    return {
        "mode": "observational",
        "action": command,
        "backend_owned": True,
    }
