from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from packages.auth import ProjectScopeError

from .credentials import ExecutionCredentialSlot, ExecutionCredentialSlotRequest, LocalEnvCredentialSlotStore
from .models import ExecutionCommandStatus, ExecutionLaneCommand, ExecutionLaneProfile, ExecutionLaneReport
from .nautilus_runtime import NautilusTradingNodeRuntimePlan, build_trading_node_runtime_plan
from .sessions import ExecutionLaneSession, TradingNodeSessionRunner, default_session_runner


class ExecutionLaneService:
    """In-memory contract service for a strategy-decoupled execution lane."""

    def __init__(
        self,
        *,
        credential_env_dir: str | Path | None = None,
        session_runner: TradingNodeSessionRunner | None = None,
        max_reports: int | None = None,
        max_sessions: int | None = None,
    ) -> None:
        self._max_reports = max_reports
        self._max_sessions = max_sessions
        self._profiles: dict[str, ExecutionLaneProfile] = {}
        self._commands: dict[str, ExecutionLaneCommand] = {}
        self._idempotency_index: dict[tuple[str, str], str] = {}
        self._reports: dict[str, ExecutionLaneReport] = {}
        self._credential_store = LocalEnvCredentialSlotStore(base_dir=credential_env_dir)
        self._credential_slots: dict[str, ExecutionCredentialSlot] = {}
        self._sessions: dict[str, ExecutionLaneSession] = {}
        self.session_runner = session_runner or default_session_runner()

    def create_credential_slot(self, payload: dict[str, object]) -> ExecutionCredentialSlot:
        request = ExecutionCredentialSlotRequest.model_validate(payload)
        slot = self._credential_store.create_slot(request)
        self._credential_slots[slot.credential_slot_ref] = slot
        return slot

    def get_credential_slot(self, credential_slot_ref: str) -> ExecutionCredentialSlot:
        return self._credential_slots[credential_slot_ref]

    def resolve_credential_slot_values(self, credential_slot_ref: str) -> dict[str, str]:
        slot = self.get_credential_slot(credential_slot_ref)
        return self._credential_store.resolve_slot_values(slot)

    def register_profile(self, payload: dict[str, object]) -> ExecutionLaneProfile:
        profile = ExecutionLaneProfile.model_validate(payload)
        self._assert_profile_credential_slot(profile)
        self._profiles[profile.runtime_profile_id] = profile
        return profile

    def get_profile(self, runtime_profile_id: str, *, project_id: str | None = None) -> ExecutionLaneProfile:
        profile = self._profiles[runtime_profile_id]
        if project_id is not None and profile.project_id != project_id:
            raise ProjectScopeError(f"execution lane profile {runtime_profile_id} is outside project scope")
        return profile

    def get_command(self, command_id: str, *, project_id: str | None = None) -> ExecutionLaneCommand:
        command = self._commands[command_id]
        if project_id is not None and command.project_id != project_id:
            raise ProjectScopeError(f"execution lane command {command_id} is outside project scope")
        return command

    def build_trading_node_runtime_plan(
        self,
        *,
        runtime_profile_id: str,
        command_id: str | None = None,
        project_id: str | None = None,
    ) -> NautilusTradingNodeRuntimePlan:
        profile = self.get_profile(runtime_profile_id, project_id=project_id)
        command = self.get_command(command_id, project_id=project_id) if command_id is not None else None
        return build_trading_node_runtime_plan(profile, command=command)

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

    def list_commands(
        self,
        *,
        runtime_profile_id: str | None = None,
        project_id: str | None = None,
    ) -> list[ExecutionLaneCommand]:
        commands = list(self._commands.values())
        if runtime_profile_id is not None:
            commands = [command for command in commands if command.runtime_profile_id == runtime_profile_id]
        if project_id is not None:
            commands = [command for command in commands if command.project_id == project_id]
        return commands

    def claim_next(self, *, runtime_profile_id: str, worker_id: str) -> ExecutionLaneCommand:
        for command in self._commands.values():
            if command.runtime_profile_id == runtime_profile_id and command.status == ExecutionCommandStatus.QUEUED:
                return self.claim_command(command_id=command.command_id or "", worker_id=worker_id)
        raise KeyError("no queued execution lane command")

    def claim_command(self, *, command_id: str, worker_id: str) -> ExecutionLaneCommand:
        command = self._commands[command_id]
        if command.status != ExecutionCommandStatus.QUEUED:
            raise ValueError("execution lane command is not queued")
        claimed = command.model_copy(
            update={
                "status": ExecutionCommandStatus.CLAIMED,
                "claimed_by": worker_id,
                "claimed_at": datetime.now(UTC).isoformat(),
            }
        )
        self._commands[claimed.command_id] = claimed
        return claimed

    def record_report(self, *, command_id: str, payload: dict[str, object]) -> ExecutionLaneReport:
        command = self._commands[command_id]
        report_payload = dict(payload)
        report_payload.setdefault("command_id", command.command_id)
        report_payload.setdefault("runtime_profile_id", command.runtime_profile_id)
        report_payload.setdefault("tenant_id", command.tenant_id)
        report_payload.setdefault("project_id", command.project_id)
        report_payload.setdefault("lane_mode", command.lane_mode)
        report_payload.setdefault("adapter_id", command.adapter_id)
        report_payload.setdefault("venue", command.venue)
        report_payload.setdefault("venue_account_id", command.venue_account_id)
        report_payload.setdefault("instrument_id", command.order_intent.get("instrument_id", "UNKNOWN"))
        report_payload.setdefault("payload", {})
        report = ExecutionLaneReport.model_validate(report_payload)
        self._reports[report.report_id] = report
        self._evict_reports_if_needed()
        self._commands[command.command_id] = command.model_copy(update={"status": ExecutionCommandStatus.REPORTED})
        return report

    def record_session(self, session: ExecutionLaneSession) -> ExecutionLaneSession:
        self._sessions[session.session_id] = session
        self._evict_sessions_if_needed()
        return session

    def _evict_reports_if_needed(self) -> None:
        if self._max_reports is not None:
            while len(self._reports) > self._max_reports:
                oldest_key = next(iter(self._reports))
                del self._reports[oldest_key]

    def _evict_sessions_if_needed(self) -> None:
        if self._max_sessions is not None:
            while len(self._sessions) > self._max_sessions:
                oldest_key = next(iter(self._sessions))
                del self._sessions[oldest_key]

    def get_session(self, session_id: str, *, project_id: str | None = None) -> ExecutionLaneSession:
        session = self._sessions[session_id]
        if project_id is not None and session.project_id != project_id:
            raise ProjectScopeError(f"execution lane session {session_id} is outside project scope")
        return session

    def list_sessions(
        self,
        *,
        runtime_profile_id: str | None = None,
        project_id: str | None = None,
    ) -> list[ExecutionLaneSession]:
        sessions = list(self._sessions.values())
        if runtime_profile_id is not None:
            sessions = [session for session in sessions if session.runtime_profile_id == runtime_profile_id]
        if project_id is not None:
            sessions = [session for session in sessions if session.project_id == project_id]
        return sessions

    def snapshot(self, *, runtime_profile_id: str | None = None, project_id: str | None = None) -> dict[str, object]:
        commands = self.list_commands(runtime_profile_id=runtime_profile_id, project_id=project_id)
        reports = list(self._reports.values())
        if runtime_profile_id is not None:
            reports = [report for report in reports if report.runtime_profile_id == runtime_profile_id]
        if project_id is not None:
            reports = [report for report in reports if report.project_id == project_id]
        sessions = self.list_sessions(runtime_profile_id=runtime_profile_id, project_id=project_id)
        profiles = self.list_profiles(project_id=project_id)
        if runtime_profile_id is not None:
            profiles = [profile for profile in profiles if profile.runtime_profile_id == runtime_profile_id]
        credential_slots = list(self._credential_slots.values())
        if project_id is not None:
            credential_slots = [slot for slot in credential_slots if slot.project_id == project_id]
        return {
            "mode": "execution_lane",
            "runtime_profile_id": runtime_profile_id,
            "profiles": len(profiles),
            "queued_commands": sum(command.status == ExecutionCommandStatus.QUEUED for command in commands),
            "claimed_commands": sum(command.status == ExecutionCommandStatus.CLAIMED for command in commands),
            "reported_commands": sum(command.status == ExecutionCommandStatus.REPORTED for command in commands),
            "reports": len(reports),
            "sessions": len(sessions),
            "running_sessions": sum(session.lifecycle_status == "RUNNING" for session in sessions),
            "credential_slots": len(credential_slots),
            "strategy_lane_coupled": False,
            "may_submit_order": any(command.may_submit_order for command in commands),
            "venue_bindings": [
                {
                    "runtime_profile_id": profile.runtime_profile_id,
                    "adapter_id": profile.adapter_id,
                    "venue": profile.venue,
                    "venue_account_id": profile.venue_account_id,
                    "lane_mode": profile.lane_mode.value,
                    "enabled": profile.enabled,
                }
                for profile in profiles
                if profile.adapter_id and profile.venue
            ],
            "ui_features": {
                "execution_lane_ui_enabled": any(profile.ui_enabled for profile in profiles),
                "paper_controls_enabled": any(profile.enabled and profile.paper_controls_enabled and profile.lane_mode.value == "paper" for profile in profiles),
                "live_controls_enabled": any(profile.live_controls_enabled and profile.is_live_enabled for profile in profiles),
                "credential_inputs_allowed": False,
                "strategy_lane_coupled": False,
            },
        }

    def _assert_profile_credential_slot(self, profile: ExecutionLaneProfile) -> None:
        if profile.credential_slot_ref is None:
            return
        if not profile.credential_slot_ref.startswith("credslot://local-env/"):
            return
        slot = self._credential_slots.get(profile.credential_slot_ref)
        if slot is None:
            raise ValueError("credential slot is not registered")
        if slot.tenant_id != profile.tenant_id or slot.project_id != profile.project_id:
            raise ValueError("credential slot scope does not match runtime profile")
        if slot.runtime_profile_id != profile.runtime_profile_id:
            raise ValueError("credential slot runtime_profile_id does not match runtime profile")
        if slot.adapter_id != profile.adapter_id or slot.venue != profile.venue:
            raise ValueError("credential slot adapter/venue does not match runtime profile")
        if slot.lane_mode != profile.lane_mode:
            raise ValueError("credential slot lane mode does not match runtime profile")

    @staticmethod
    def _assert_profile_matches_command(profile: ExecutionLaneProfile, command: ExecutionLaneCommand) -> None:
        if profile.tenant_id != command.tenant_id or profile.project_id != command.project_id:
            raise ValueError("execution lane command scope does not match runtime profile")
        if profile.lane_mode != command.lane_mode:
            raise ValueError("execution lane command mode does not match runtime profile")
        if profile.adapter_id != command.adapter_id:
            raise ValueError("execution lane command adapter_id does not match runtime profile")
        if profile.venue != command.venue:
            raise ValueError("execution lane command venue does not match runtime profile")
        if profile.venue_account_id and command.venue_account_id and profile.venue_account_id != command.venue_account_id:
            raise ValueError("execution lane command venue_account_id does not match runtime profile")
        if command.may_submit_order or command.execution_authority or command.live_trading_enabled:
            if not profile.is_live_enabled:
                raise ValueError("execution lane profile is not live-enabled")
            if profile.risk_profile_id != command.risk_profile_id:
                raise ValueError("execution lane command risk profile does not match runtime profile")
            if profile.credential_slot_ref != command.credential_slot_ref:
                raise ValueError("execution lane command credential slot does not match runtime profile")
            for field_name in (
                "manual_review_id",
                "data_tester_evidence_ref",
                "exec_tester_evidence_ref",
                "reconciliation_evidence_ref",
            ):
                if getattr(profile, field_name) != getattr(command, field_name):
                    raise ValueError(f"execution lane command {field_name} does not match runtime profile")


_default_service: ExecutionLaneService | None = None


def default_execution_lane_service() -> ExecutionLaneService:
    global _default_service
    if _default_service is None:
        _default_service = ExecutionLaneService()
    return _default_service


def reset_default_execution_lane_service() -> None:
    global _default_service
    _default_service = None
