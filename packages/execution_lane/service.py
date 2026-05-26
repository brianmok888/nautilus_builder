from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from .models import ExecutionCommandStatus, ExecutionLaneCommand, ExecutionLaneProfile, ExecutionLaneReport


class ExecutionLaneService:
    """In-memory contract service for a strategy-decoupled execution lane."""

    def __init__(self) -> None:
        self._profiles: dict[str, ExecutionLaneProfile] = {}
        self._commands: dict[str, ExecutionLaneCommand] = {}
        self._idempotency_index: dict[tuple[str, str], str] = {}
        self._reports: dict[str, ExecutionLaneReport] = {}

    def register_profile(self, payload: dict[str, object]) -> ExecutionLaneProfile:
        profile = ExecutionLaneProfile.model_validate(payload)
        self._profiles[profile.runtime_profile_id] = profile
        return profile

    def get_profile(self, runtime_profile_id: str) -> ExecutionLaneProfile:
        return self._profiles[runtime_profile_id]

    def list_profiles(self, *, project_id: str | None = None) -> list[ExecutionLaneProfile]:
        profiles = list(self._profiles.values())
        if project_id is not None:
            profiles = [profile for profile in profiles if profile.project_id == project_id]
        return profiles

    def enqueue_command(self, payload: dict[str, object]) -> ExecutionLaneCommand:
        command = ExecutionLaneCommand.model_validate(payload)
        profile = self._profiles.get(command.runtime_profile_id)
        if profile is None:
            raise ValueError("execution lane profile is required")
        self._assert_profile_matches_command(profile, command)
        key = (command.runtime_profile_id, command.idempotency_key)
        existing_id = self._idempotency_index.get(key)
        if existing_id is not None:
            return self._commands[existing_id]
        self._commands[command.command_id] = command
        self._idempotency_index[key] = command.command_id
        return command

    def list_commands(self, *, runtime_profile_id: str | None = None) -> list[ExecutionLaneCommand]:
        commands = list(self._commands.values())
        if runtime_profile_id is not None:
            commands = [command for command in commands if command.runtime_profile_id == runtime_profile_id]
        return commands

    def claim_next(self, *, runtime_profile_id: str, worker_id: str) -> ExecutionLaneCommand:
        for command in self._commands.values():
            if command.runtime_profile_id == runtime_profile_id and command.status == ExecutionCommandStatus.QUEUED:
                claimed = command.model_copy(
                    update={
                        "status": ExecutionCommandStatus.CLAIMED,
                        "claimed_by": worker_id,
                        "claimed_at": datetime.now(UTC).isoformat(),
                    }
                )
                self._commands[claimed.command_id] = claimed
                return claimed
        raise KeyError("no queued execution lane command")

    def record_report(self, *, command_id: str, payload: dict[str, object]) -> ExecutionLaneReport:
        command = self._commands[command_id]
        report_payload = dict(payload)
        report_payload.setdefault("command_id", command.command_id)
        report_payload.setdefault("runtime_profile_id", command.runtime_profile_id)
        report_payload.setdefault("tenant_id", command.tenant_id)
        report_payload.setdefault("project_id", command.project_id)
        report_payload.setdefault("lane_mode", command.lane_mode)
        report_payload.setdefault("venue", command.order_intent.get("venue", command.order_intent.get("instrument_id", "SIM")))
        report_payload.setdefault("instrument_id", command.order_intent.get("instrument_id", "UNKNOWN"))
        report_payload.setdefault("payload", {})
        report = ExecutionLaneReport.model_validate(report_payload)
        self._reports[report.report_id] = report
        self._commands[command.command_id] = command.model_copy(update={"status": ExecutionCommandStatus.REPORTED})
        return report

    def snapshot(self, *, runtime_profile_id: str | None = None) -> dict[str, object]:
        commands = self.list_commands(runtime_profile_id=runtime_profile_id)
        reports = list(self._reports.values())
        if runtime_profile_id is not None:
            reports = [report for report in reports if report.runtime_profile_id == runtime_profile_id]
        return {
            "mode": "execution_lane",
            "runtime_profile_id": runtime_profile_id,
            "profiles": len(self.list_profiles()),
            "queued_commands": sum(command.status == ExecutionCommandStatus.QUEUED for command in commands),
            "claimed_commands": sum(command.status == ExecutionCommandStatus.CLAIMED for command in commands),
            "reported_commands": sum(command.status == ExecutionCommandStatus.REPORTED for command in commands),
            "reports": len(reports),
            "strategy_lane_coupled": False,
            "may_submit_order": any(command.may_submit_order for command in commands),
        }

    @staticmethod
    def _assert_profile_matches_command(profile: ExecutionLaneProfile, command: ExecutionLaneCommand) -> None:
        if profile.tenant_id != command.tenant_id or profile.project_id != command.project_id:
            raise ValueError("execution lane command scope does not match runtime profile")
        if profile.lane_mode != command.lane_mode:
            raise ValueError("execution lane command mode does not match runtime profile")
        if command.may_submit_order or command.execution_authority or command.live_trading_enabled:
            if not profile.is_live_enabled:
                raise ValueError("execution lane profile is not live-enabled")
            if profile.risk_profile_id != command.risk_profile_id:
                raise ValueError("execution lane command risk profile does not match runtime profile")
            if profile.credential_slot_ref != command.credential_slot_ref:
                raise ValueError("execution lane command credential slot does not match runtime profile")


_default_service: ExecutionLaneService | None = None


def default_execution_lane_service() -> ExecutionLaneService:
    global _default_service
    if _default_service is None:
        _default_service = ExecutionLaneService()
    return _default_service


def reset_default_execution_lane_service() -> None:
    global _default_service
    _default_service = None
