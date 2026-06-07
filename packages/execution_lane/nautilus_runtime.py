from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from .config_contract import DataClientEntry, ExecClientEntry, ExecEngineConfig, RiskEngineConfig, TradingNodeConfigContract
from .models import ExecutionLaneCommand, ExecutionLaneMode, ExecutionLaneProfile


NAUTILUS_TRADING_NODE_IMPORTS = [
    "nautilus_trader.config.TradingNodeConfig",
    "nautilus_trader.config.LiveExecEngineConfig",
    "nautilus_trader.live.node.TradingNode",
]


class NautilusTradingNodeRuntimePlan(BaseModel):
    """Auditable Builder contract for a Nautilus TradingNode execution lane."""

    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["execution_lane.tradingnode.v1"] = "execution_lane.tradingnode.v1"
    tenant_id: str = Field(min_length=1)
    project_id: str = Field(min_length=1)
    runtime_profile_id: str = Field(min_length=1)
    lane_mode: ExecutionLaneMode
    readiness_status: Literal["READY", "BLOCKED"]
    blocked_reasons: list[str] = Field(default_factory=list)
    node_runtime: Literal["python_trading_node"] = "python_trading_node"
    runtime_label: str = "python_live_integration_specific"
    future_runtime: Literal["rust_live_node"] = "rust_live_node"
    runtime_environment: Literal["sandbox", "live"]
    adapter_id: str = Field(min_length=1)
    venue: str = Field(min_length=1)
    venue_account_id: str | None = None
    strategy_lane_coupled: Literal[False] = False
    browser_credentials_allowed: Literal[False] = False
    credential_inputs_allowed: Literal[False] = False
    live_trading_enabled: bool = False
    execution_authority: bool = False
    may_submit_order: bool = False
    advisory_only: bool = True
    manual_review_required: bool = True
    reconciliation_required: bool = True
    credential_slot_ref: str | None = None
    risk_profile_id: str | None = None
    strategy_lineage_id: str | None = None
    strategy_version_id: str | None = None
    trade_action_id: str | None = None
    promotion_approval_id: str | None = None
    manual_review_id: str | None = None
    config_checksum: str | None = None
    evidence_refs: dict[str, str] = Field(default_factory=dict)
    nautilus_imports: list[str] = Field(default_factory=lambda: list(NAUTILUS_TRADING_NODE_IMPORTS))
    config_contract: TradingNodeConfigContract
    nautilus_trader_version: str | None = None

    @field_validator("runtime_label")
    @classmethod
    def validate_runtime_label(cls, value: str) -> str:
        _KNOWN_RUNTIME_LABELS = {"python_live_integration_specific", "rust_live_node"}
        if value not in _KNOWN_RUNTIME_LABELS:
            raise ValueError(f"runtime_label must be one of {_KNOWN_RUNTIME_LABELS}, got: {value}")
        return value


def build_trading_node_runtime_plan(
    profile: ExecutionLaneProfile,
    *,
    command: ExecutionLaneCommand | None = None,
) -> NautilusTradingNodeRuntimePlan:
    """Build a fail-closed Nautilus TradingNode runtime plan without starting a node.

    Builder owns contract validation and audit metadata here. The live adapter
    itself still needs DataTester, ExecTester, and reconciliation evidence before
    any command may carry order authority.
    """

    _assert_command_matches_profile(profile, command)
    reasons = _profile_blocked_reasons(profile)
    if command is not None:
        reasons.extend(_command_blocked_reasons(profile, command))
    reasons = sorted(set(reasons))

    live_ready = profile.lane_mode == ExecutionLaneMode.LIVE and not reasons and profile.is_live_enabled
    paper_ready = (
        profile.lane_mode == ExecutionLaneMode.PAPER
        and not reasons
        and profile.enabled
        and profile.paper_trading_enabled
        and profile.adapter_id is not None
        and profile.venue is not None
    )
    ready = live_ready or paper_ready
    credential_slot_bound = ready and profile.credential_slot_ref is not None
    runtime_environment: Literal["sandbox", "live"] = "live" if profile.lane_mode == ExecutionLaneMode.LIVE else "sandbox"

    return NautilusTradingNodeRuntimePlan(
        tenant_id=profile.tenant_id,
        project_id=profile.project_id,
        runtime_profile_id=profile.runtime_profile_id,
        lane_mode=profile.lane_mode,
        readiness_status="READY" if ready else "BLOCKED",
        blocked_reasons=reasons,
        runtime_environment=runtime_environment,
        adapter_id=profile.adapter_id or "UNBOUND",
        venue=profile.venue or "UNBOUND",
        venue_account_id=profile.venue_account_id,
        live_trading_enabled=profile.live_trading_enabled if live_ready else False,
        execution_authority=profile.execution_authority if live_ready else False,
        may_submit_order=profile.may_submit_order if live_ready else False,
        advisory_only=profile.advisory_only,
        manual_review_required=profile.manual_review_required,
        reconciliation_required=profile.reconciliation_required,
        credential_slot_ref=profile.credential_slot_ref if credential_slot_bound else None,
        risk_profile_id=profile.risk_profile_id,
        strategy_lineage_id=command.strategy_lineage_id if command is not None else None,
        strategy_version_id=command.strategy_version_id if command is not None else None,
        trade_action_id=command.trade_action_id if command is not None else None,
        promotion_approval_id=command.promotion_approval_id if command is not None else None,
        manual_review_id=profile.manual_review_id,
        config_checksum=profile.config_checksum,
        evidence_refs=_evidence_refs(profile),
        config_contract=_config_contract(profile=profile, live_ready=live_ready, credential_slot_bound=credential_slot_bound),
        nautilus_trader_version=profile.nautilus_trader_version or _installed_nautilus_version(),
    )


def _assert_command_matches_profile(profile: ExecutionLaneProfile, command: ExecutionLaneCommand | None) -> None:
    if command is None:
        return
    if profile.tenant_id != command.tenant_id or profile.project_id != command.project_id:
        raise ValueError("execution lane command scope does not match runtime profile")
    if profile.runtime_profile_id != command.runtime_profile_id:
        raise ValueError("execution lane command runtime_profile_id does not match runtime profile")
    if profile.lane_mode != command.lane_mode:
        raise ValueError("execution lane command mode does not match runtime profile")
    if profile.adapter_id != command.adapter_id:
        raise ValueError("execution lane command adapter_id does not match runtime profile")
    if profile.venue != command.venue:
        raise ValueError("execution lane command venue does not match runtime profile")


def _profile_blocked_reasons(profile: ExecutionLaneProfile) -> list[str]:
    reasons: list[str] = []
    if not profile.enabled:
        reasons.append("enabled")
    if profile.adapter_id is None or profile.adapter_id.strip() == "":
        reasons.append("adapter_id")
    if profile.venue is None or profile.venue.strip() == "":
        reasons.append("venue")
    if profile.lane_mode == ExecutionLaneMode.PAPER:
        if not profile.paper_trading_enabled:
            reasons.append("paper_trading_enabled")
        if profile.live_trading_enabled:
            reasons.append("paper_live_trading_enabled_forbidden")
        if profile.execution_authority:
            reasons.append("paper_execution_authority_forbidden")
        if profile.may_submit_order:
            reasons.append("paper_may_submit_order_forbidden")
        return reasons

    if profile.lane_mode == ExecutionLaneMode.LIVE:
        if profile.advisory_only:
            reasons.append("advisory_only=false")
        if not profile.manual_review_required:
            reasons.append("manual_review_required")
        if not profile.reconciliation_required:
            reasons.append("reconciliation_required")
        if not profile.live_trading_enabled:
            reasons.append("live_trading_enabled")
        if not profile.execution_authority:
            reasons.append("execution_authority")
        if not profile.may_submit_order:
            reasons.append("may_submit_order")
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
            if _blank(getattr(profile, field_name)):
                reasons.append(field_name)
        return reasons

    return reasons


def _command_blocked_reasons(profile: ExecutionLaneProfile, command: ExecutionLaneCommand) -> list[str]:
    if profile.lane_mode == ExecutionLaneMode.PAPER:
        return []
    reasons: list[str] = []
    if not command.live_trading_enabled:
        reasons.append("command.live_trading_enabled")
    if not command.execution_authority:
        reasons.append("command.execution_authority")
    if not command.may_submit_order:
        reasons.append("command.may_submit_order")
    if command.risk_profile_id != profile.risk_profile_id:
        reasons.append("command.risk_profile_id")
    if command.credential_slot_ref != profile.credential_slot_ref:
        reasons.append("command.credential_slot_ref")
    if command.risk_decision.get("status") != "approved":
        reasons.append("command.risk_decision.status=approved")
    for field_name in (
        "promotion_approval_id",
        "manual_review_id",
        "data_tester_evidence_ref",
        "exec_tester_evidence_ref",
        "reconciliation_evidence_ref",
    ):
        if _blank(getattr(command, field_name)):
            reasons.append(f"command.{field_name}")
    for field_name in (
        "manual_review_id",
        "data_tester_evidence_ref",
        "exec_tester_evidence_ref",
        "reconciliation_evidence_ref",
    ):
        if getattr(command, field_name) != getattr(profile, field_name):
            reasons.append(f"command.{field_name}")
    return reasons


def _config_contract(*, profile: ExecutionLaneProfile, live_ready: bool, credential_slot_bound: bool) -> TradingNodeConfigContract:
    credential_slot_ref = profile.credential_slot_ref if credential_slot_bound else None
    return TradingNodeConfigContract(
        runtime_note="Python TradingNode integration-specific plan; Rust LiveNode is the future runtime target.",
        trader_id=f"BUILDER-{profile.project_id[:24]}",
        environment="live" if profile.lane_mode == ExecutionLaneMode.LIVE else "sandbox",
        data_clients={
            profile.venue or "UNBOUND": DataClientEntry(
                adapter_id=profile.adapter_id,
                venue_account_id=profile.venue_account_id,
                credential_slot_ref=credential_slot_ref,
            )
        },
        exec_clients={
            profile.venue or "UNBOUND": ExecClientEntry(
                adapter_id=profile.adapter_id,
                venue_account_id=profile.venue_account_id,
                credential_slot_ref=credential_slot_ref,
                paper_mode=profile.lane_mode == ExecutionLaneMode.PAPER,
                live_authority=live_ready,
            )
        },
        exec_engine=ExecEngineConfig(
            reconciliation=True,
            reconciliation_lookback_mins=max(60, profile.reconciliation_lookback_mins),
            reconciliation_startup_delay_secs=profile.reconciliation_startup_delay_secs,
            open_check_lookback_mins=max(60, profile.reconciliation_lookback_mins),
            position_check_lookback_mins=max(60, profile.reconciliation_lookback_mins),
        ),
        risk_engine=RiskEngineConfig(
            risk_profile_id=profile.risk_profile_id,
        ),
    )


def _evidence_refs(profile: ExecutionLaneProfile) -> dict[str, str]:
    refs: dict[str, str] = {}
    if profile.data_tester_evidence_ref:
        refs["data_tester"] = profile.data_tester_evidence_ref
    if profile.exec_tester_evidence_ref:
        refs["exec_tester"] = profile.exec_tester_evidence_ref
    if profile.reconciliation_evidence_ref:
        refs["reconciliation"] = profile.reconciliation_evidence_ref
    if profile.manual_review_id:
        refs["manual_review"] = profile.manual_review_id
    return refs


def _blank(value: object) -> bool:
    return value is None or str(value).strip() == ""


def _installed_nautilus_version() -> str | None:
    try:
        import nautilus_trader
    except Exception:
        return None
    return str(getattr(nautilus_trader, "__version__", "") or "") or None
