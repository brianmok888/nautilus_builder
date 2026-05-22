from __future__ import annotations


ALLOWED_TERMINAL_COMMANDS = ["status", "help", "metrics", "validation", "replay", "cancel"]


def run_terminal_command(command: str) -> dict[str, object]:
    if command not in ALLOWED_TERMINAL_COMMANDS:
        raise ValueError("command not allowed")

    if command == "cancel":
        return {
            "mode": "observational",
            "action": "cancel_request",
            "backend_owned": True,
        }

    return {
        "mode": "observational",
        "action": command,
        "backend_owned": True,
    }
