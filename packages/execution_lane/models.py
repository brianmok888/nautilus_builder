from __future__ import annotations

import hashlib
import json
from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


_SECRET_KEYS = {"api_key", "secret", "secret_key", "password", "private_key", "credential", "credentials", "authorization", "token"}
_STRATEGY_COUPLING_KEYS = {
    "strategy_runtime_id",
    "strategy_process_id",
    "strategy_lane_id",
    "strategy_worker_id",
    "strategy_actor_id",
}
_SHA256_LEN = 64


class ExecutionLaneMode(str, Enum):
    PAPER = "paper"
    LIVE = "live"


class ExecutionLaneStatus(str, Enum):
    CREATED = "CREATED"
    RUNNING = "RUNNING"
    STOPPED = "STOPPED"


class ExecutionCommandStatus(str, Enum):
    QUEUED = "QUEUED"
    CLAIMED = "CLAIMED"
    REPORTED = "REPORTED"
    REJECTED = "REJECTED"


class ExecutionLaneProfile(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tenant_id: str = Field(min_length=1)
    project_id: str = Field(min_length=1)
    runtime_profile_id: str = Field(min_length=1)
    profile_name: str = Field(min_length=1)
    lane_mode: ExecutionLaneMode
    enabled: bool = False
    status: ExecutionLaneStatus = ExecutionLaneStatus.CREATED
    consumes_stream: str = Field(min_length=1)
    adapter_id: str | None = None
    venue: str | None = None
    venue_account_id: str | None = None
    ui_enabled: bool = False
    paper_controls_enabled: bool = False
    live_controls_enabled: bool = False
    strategy_lane_coupled: Literal[False] = False
    advisory_only: bool = True
    manual_review_required: bool = True
    paper_trading_enabled: bool = False
    live_trading_enabled: bool = False
    execution_authority: bool = False
    may_submit_order: bool = False
    risk_profile_id: str | None = None
    reconciliation_required: bool = True
    credential_slot_ref: str | None = None
    activated_by: str | None = None
    activated_at: str | None = None
    config_checksum: str | None = None
    manual_review_id: str | None = None
    data_tester_evidence_ref: str | None = None
    exec_tester_evidence_ref: str | None = None
    reconciliation_evidence_ref: str | None = None
    reconciliation_lookback_mins: int = Field(default=60, ge=60)
    reconciliation_startup_delay_secs: float = Field(default=10.0, ge=10.0)
    nautilus_trader_version: str | None = None

    @model_validator(mode="before")
    @classmethod
    def reject_strategy_coupling_fields(cls, data: object) -> object:
        if isinstance(data, dict):
            _assert_no_forbidden_keys(data, forbidden=_SECRET_KEYS, message="credentials are not allowed in execution lane profiles")
            _assert_no_forbidden_keys(data, forbidden=_STRATEGY_COUPLING_KEYS, message="strategy lane coupling fields are not allowed")
        return data

    @model_validator(mode="after")
    def validate_authority(self) -> "ExecutionLaneProfile":
        if self.enabled:
            missing_binding = [name for name in ("adapter_id", "venue") if not _present(getattr(self, name))]
            if missing_binding:
                raise ValueError(f"enabled execution lane profile requires {', '.join(missing_binding)}")

        if self.lane_mode == ExecutionLaneMode.PAPER:
            if self.live_trading_enabled or self.execution_authority or self.may_submit_order:
                raise ValueError("paper execution lanes cannot enable live authority")
            if self.enabled and not self.paper_trading_enabled:
                raise ValueError("enabled paper execution lanes require paper_trading_enabled")
            if self.live_controls_enabled:
                raise ValueError("live UI controls require live authority")
            return self

        if self.lane_mode == ExecutionLaneMode.LIVE:
            wants_live_authority = self.live_trading_enabled or self.execution_authority or self.may_submit_order
            if not wants_live_authority:
                if self.live_controls_enabled:
                    raise ValueError("live UI controls require live authority")
                return self
            missing = []
            if not self.enabled:
                missing.append("enabled")
            if self.advisory_only:
                missing.append("advisory_only=false")
            if not self.manual_review_required:
                missing.append("manual_review_required")
            if not self.reconciliation_required:
                missing.append("reconciliation_required")
            if not self.live_trading_enabled:
                missing.append("live_trading_enabled")
            if not self.execution_authority:
                missing.append("execution_authority")
            if not self.may_submit_order:
                missing.append("may_submit_order")
            for field_name in (
                "risk_profile_id",
                "credential_slot_ref",
                "activated_by",
                "activated_at",
                "config_checksum",
                "manual_review_id",
                "data_tester_evidence_ref",
                "exec_tester_evidence_ref",
                "reconciliation_evidence_ref",
            ):
                if not _present(getattr(self, field_name)):
                    missing.append(field_name)
            if self.config_checksum is not None and len(self.config_checksum) != _SHA256_LEN:
                missing.append("config_checksum_sha256")
            if missing:
                raise ValueError(f"live execution profile missing gates: {', '.join(missing)}")
            return self

        return self

    @property
    def is_live_enabled(self) -> bool:
        return (
            self.lane_mode == ExecutionLaneMode.LIVE
            and self.enabled
            and self.live_trading_enabled
            and self.execution_authority
            and self.may_submit_order
            and not self.advisory_only
            and self.manual_review_required
            and self.reconciliation_required
            and _present(self.risk_profile_id)
            and _present(self.credential_slot_ref)
            and _present(self.activated_by)
            and _present(self.activated_at)
            and _present(self.config_checksum)
            and _present(self.manual_review_id)
            and _present(self.data_tester_evidence_ref)
            and _present(self.exec_tester_evidence_ref)
            and _present(self.reconciliation_evidence_ref)
        )


class ExecutionLaneCommand(BaseModel):
    model_config = ConfigDict(extra="forbid")

    command_id: str | None = None
    tenant_id: str = Field(min_length=1)
    project_id: str = Field(min_length=1)
    runtime_profile_id: str = Field(min_length=1)
    lane_mode: ExecutionLaneMode
    adapter_id: str = Field(min_length=1)
    venue: str = Field(min_length=1)
    venue_account_id: str | None = None
    trade_action_id: str = Field(min_length=1)
    source_event_id: str = Field(min_length=1)
    idempotency_key: str = Field(min_length=1)
    strategy_lineage_id: str = Field(min_length=1)
    strategy_version_id: str = Field(min_length=1)
    order_intent: dict[str, Any]
    risk_decision: dict[str, Any] = Field(default_factory=dict)
    promotion_approval_id: str | None = None
    risk_profile_id: str | None = None
    reconciliation_required: bool = True
    credential_slot_ref: str | None = None
    manual_review_id: str | None = None
    data_tester_evidence_ref: str | None = None
    exec_tester_evidence_ref: str | None = None
    reconciliation_evidence_ref: str | None = None
    live_trading_enabled: bool = False
    execution_authority: bool = False
    may_submit_order: bool = False
    strategy_lane_coupled: Literal[False] = False
    status: ExecutionCommandStatus = ExecutionCommandStatus.QUEUED
    claimed_by: str | None = None
    claimed_at: str | None = None

    @model_validator(mode="before")
    @classmethod
    def populate_command_id_and_reject_coupling(cls, data: object) -> object:
        if isinstance(data, dict):
            _assert_no_forbidden_keys(data, forbidden=_STRATEGY_COUPLING_KEYS, message="strategy lane coupling fields are not allowed")
            candidate = dict(data)
            if not candidate.get("command_id"):
                material = {
                    "tenant_id": candidate.get("tenant_id"),
                    "project_id": candidate.get("project_id"),
                    "runtime_profile_id": candidate.get("runtime_profile_id"),
                    "trade_action_id": candidate.get("trade_action_id"),
                    "source_event_id": candidate.get("source_event_id"),
                    "idempotency_key": candidate.get("idempotency_key"),
                    "strategy_lineage_id": candidate.get("strategy_lineage_id"),
                    "strategy_version_id": candidate.get("strategy_version_id"),
                }
                candidate["command_id"] = f"exec_cmd_{_sha256_hex(material)[:16]}"
            return candidate
        return data

    @field_validator("order_intent", "risk_decision")
    @classmethod
    def reject_secrets_and_coupling_in_payloads(cls, value: dict[str, Any]) -> dict[str, Any]:
        _assert_no_forbidden_keys(value, forbidden=_SECRET_KEYS, message="credentials are not allowed in execution lane payloads")
        _assert_no_forbidden_keys(value, forbidden=_STRATEGY_COUPLING_KEYS, message="strategy lane coupling fields are not allowed")
        return value

    @model_validator(mode="after")
    def validate_authority(self) -> "ExecutionLaneCommand":
        wants_live_authority = self.live_trading_enabled or self.execution_authority or self.may_submit_order
        if self.lane_mode == ExecutionLaneMode.PAPER:
            if wants_live_authority:
                raise ValueError("paper execution commands cannot enable live authority")
            return self

        if self.lane_mode == ExecutionLaneMode.LIVE:
            if not wants_live_authority:
                return self
            missing = []
            if not self.live_trading_enabled:
                missing.append("live_trading_enabled")
            if not self.execution_authority:
                missing.append("execution_authority")
            if not self.may_submit_order:
                missing.append("may_submit_order")
            if not self.reconciliation_required:
                missing.append("reconciliation_required")
            for field_name in (
                "promotion_approval_id",
                "risk_profile_id",
                "credential_slot_ref",
                "manual_review_id",
                "data_tester_evidence_ref",
                "exec_tester_evidence_ref",
                "reconciliation_evidence_ref",
            ):
                if not _present(getattr(self, field_name)):
                    missing.append(field_name)
            if str(self.risk_decision.get("status", "")).lower() != "approved":
                missing.append("risk_decision.status=approved")
            if missing:
                raise ValueError(f"live execution command missing gates: {', '.join(missing)}")
            return self

        return self


class ExecutionLaneReport(BaseModel):
    model_config = ConfigDict(extra="forbid")

    report_id: str | None = None
    command_id: str = Field(min_length=1)
    runtime_profile_id: str = Field(min_length=1)
    tenant_id: str = Field(min_length=1)
    project_id: str = Field(min_length=1)
    lane_mode: ExecutionLaneMode
    adapter_id: str = Field(min_length=1)
    venue_account_id: str | None = None
    report_type: str = Field(min_length=1)
    venue: str = Field(min_length=1)
    instrument_id: str = Field(min_length=1)
    payload: dict[str, Any]
    strategy_lane_coupled: Literal[False] = False

    @model_validator(mode="before")
    @classmethod
    def populate_report_id(cls, data: object) -> object:
        if isinstance(data, dict):
            candidate = dict(data)
            if not candidate.get("report_id"):
                material = {
                    "command_id": candidate.get("command_id"),
                    "runtime_profile_id": candidate.get("runtime_profile_id"),
                    "report_type": candidate.get("report_type"),
                    "payload": candidate.get("payload", {}),
                }
                candidate["report_id"] = f"exec_report_{_sha256_hex(material)[:16]}"
            return candidate
        return data

    @field_validator("payload")
    @classmethod
    def reject_payload_secrets(cls, value: dict[str, Any]) -> dict[str, Any]:
        _assert_no_forbidden_keys(value, forbidden=_SECRET_KEYS, message="credentials are not allowed in execution reports")
        return value


def _present(value: str | None) -> bool:
    return value is not None and value.strip() != ""


def _sha256_hex(payload: dict[str, Any]) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")).hexdigest()


def _assert_no_forbidden_keys(payload: object, *, forbidden: set[str], message: str) -> None:
    if isinstance(payload, dict):
        for key, value in payload.items():
            if str(key).lower() in forbidden:
                raise ValueError(message)
            _assert_no_forbidden_keys(value, forbidden=forbidden, message=message)
    elif isinstance(payload, list):
        for value in payload:
            _assert_no_forbidden_keys(value, forbidden=forbidden, message=message)
