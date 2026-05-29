from __future__ import annotations

import hashlib
import json
import os
import threading
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, Literal, Protocol

from pydantic import BaseModel, ConfigDict, Field

from .models import ExecutionLaneCommand, ExecutionLaneMode, ExecutionLaneProfile
from .nautilus_runtime import NautilusTradingNodeRuntimePlan

PAPER_STRATEGY_PATH = "packages.execution_lane.paper_strategy:ExecutionLanePaperStrategy"
PAPER_STRATEGY_CONFIG_PATH = "packages.execution_lane.paper_strategy:ExecutionLanePaperStrategyConfig"


class ExecutionLaneSession(BaseModel):
    model_config = ConfigDict(extra="forbid")

    session_id: str = Field(min_length=1)
    command_id: str = Field(min_length=1)
    runtime_profile_id: str = Field(min_length=1)
    tenant_id: str = Field(min_length=1)
    project_id: str = Field(min_length=1)
    lane_mode: ExecutionLaneMode
    adapter_id: str = Field(min_length=1)
    venue: str = Field(min_length=1)
    venue_account_id: str | None = None
    status: Literal["INITIALIZED", "RUNNING", "STOPPED", "DISPOSED", "FAILED"]
    lifecycle_status: Literal["INITIALIZED", "RUNNING", "STOPPED", "DISPOSED", "FAILED"]
    runner_mode: str = Field(min_length=1)
    worker_id: str = Field(min_length=1)
    started_at: str
    stopped_at: str | None = None
    disposed_at: str | None = None
    runtime_environment: Literal["sandbox", "live"] = "sandbox"
    node_runtime: str = "python_trading_node"
    runtime_label: str = "python_live_integration_specific"
    future_runtime: str = "rust_live_node"
    strategy_lineage_id: str = Field(min_length=1)
    strategy_version_id: str = Field(min_length=1)
    trade_action_id: str = Field(min_length=1)
    promotion_approval_id: str | None = None
    credential_slot_ref: str = Field(min_length=1)
    credential_env_keys: list[str] = Field(default_factory=list)
    credential_values_resolved: bool = False
    tradingnode_config: dict[str, Any]
    attached_strategy: dict[str, Any]
    lifecycle_events: list[dict[str, Any]] = Field(default_factory=list)
    browser_credentials_allowed: Literal[False] = False
    credential_inputs_allowed: Literal[False] = False
    strategy_lane_coupled: Literal[False] = False
    live_trading_enabled: bool = False
    execution_authority: bool = False
    may_submit_order: bool = False


@dataclass(frozen=True)
class TradingNodeBuildResult:
    config: Any
    summary: dict[str, Any]
    attached_strategy: dict[str, Any]
    data_client_factories: dict[str, Any]
    exec_client_factories: dict[str, Any]


@dataclass(frozen=True)
class TradingNodeRunnerResult:
    runner_mode: str
    status: Literal["RUNNING", "FAILED"]
    lifecycle_events: list[dict[str, Any]]


@dataclass(frozen=True)
class TradingNodeStopResult:
    status: Literal["DISPOSED", "FAILED"]
    lifecycle_events: list[dict[str, Any]]


class TradingNodeSessionRunner(Protocol):
    runner_mode: str

    def start(
        self,
        *,
        session_id: str,
        config: Any,
        data_client_factories: dict[str, Any],
        exec_client_factories: dict[str, Any],
    ) -> TradingNodeRunnerResult: ...

    def stop(self, *, session_id: str) -> TradingNodeStopResult: ...


class ContractTradingNodeSessionRunner:
    """Deterministic safe runner for tests/local UI contracts.

    It proves Builder can build a Nautilus TradingNodeConfig and move through
    lifecycle states without opening venue sockets or giving the browser process
    authority. Set BUILDER_EXECUTION_LANE_TRADINGNODE_RUNNER=native to opt into
    an operator-managed native runner.
    """

    runner_mode = "contract_dry_run"

    def start(
        self,
        *,
        session_id: str,
        config: Any,
        data_client_factories: dict[str, Any],
        exec_client_factories: dict[str, Any],
    ) -> TradingNodeRunnerResult:
        return TradingNodeRunnerResult(
            runner_mode=self.runner_mode,
            status="RUNNING",
            lifecycle_events=[
                _event("BUILD", "TradingNode.build lifecycle acknowledged by contract runner", session_id=session_id),
                _event("RUNNING", "TradingNode.run lifecycle acknowledged by contract runner", session_id=session_id),
            ],
        )

    def stop(self, *, session_id: str) -> TradingNodeStopResult:
        return TradingNodeStopResult(
            status="DISPOSED",
            lifecycle_events=[
                _event("STOPPED", "TradingNode.stop lifecycle acknowledged by contract runner", session_id=session_id),
                _event("DISPOSED", "TradingNode.dispose lifecycle acknowledged by contract runner", session_id=session_id),
            ],
        )


class NativeTradingNodeSessionRunner:
    """Operator-opt-in Python TradingNode runner.

    The default Builder service does not select this runner. It is available for
    local/VM paper sandboxes where the operator has explicitly configured
    credentials, adapter factories, and network policy.

    This runner must NOT be used from the API event loop. Use it only from
    backend worker processes or CLI entrypoints.
    """

    runner_mode = "native_trading_node"

    def __init__(self, *, node_factory: Any | None = None) -> None:
        self._node_factory = node_factory
        self._sessions: dict[str, tuple[Any, threading.Thread]] = {}

    @staticmethod
    def _assert_not_in_async_loop() -> None:
        try:
            import asyncio
            loop = asyncio.get_running_loop()
        except RuntimeError:
            return
        raise RuntimeError(
            "NativeTradingNodeSessionRunner.start() must not be called from an asyncio event loop. "
            "Use a backend worker process or CLI entrypoint instead."
        )

    def start(
        self,
        *,
        session_id: str,
        config: Any,
        data_client_factories: dict[str, Any],
        exec_client_factories: dict[str, Any],
    ) -> TradingNodeRunnerResult:
        self._assert_not_in_async_loop()
        if not data_client_factories or not exec_client_factories:
            raise ValueError("native TradingNode runner requires concrete adapter factories")
        from nautilus_trader.live.node import TradingNode

        node_factory = self._node_factory or TradingNode
        node = node_factory(config)
        for name, factory in data_client_factories.items():
            node.add_data_client_factory(name, factory)
        for name, factory in exec_client_factories.items():
            node.add_exec_client_factory(name, factory)
        node.build()
        thread = threading.Thread(target=node.run, name=f"builder-exec-{session_id}", daemon=True)
        thread.start()
        self._sessions[session_id] = (node, thread)
        return TradingNodeRunnerResult(
            runner_mode=self.runner_mode,
            status="RUNNING",
            lifecycle_events=[
                _event("BUILD", "TradingNode.build called", session_id=session_id),
                _event("RUNNING", "TradingNode.run started in backend worker thread", session_id=session_id),
            ],
        )

    def stop(self, *, session_id: str) -> TradingNodeStopResult:
        node, thread = self._sessions.pop(session_id)
        node.stop()
        thread.join(timeout=5.0)
        node.dispose()
        return TradingNodeStopResult(
            status="DISPOSED",
            lifecycle_events=[
                _event("STOPPED", "TradingNode.stop called", session_id=session_id),
                _event("DISPOSED", "TradingNode.dispose called", session_id=session_id),
            ],
        )


def default_session_runner() -> TradingNodeSessionRunner:
    if os.getenv("BUILDER_EXECUTION_LANE_TRADINGNODE_RUNNER", "").strip().lower() == "native":
        return NativeTradingNodeSessionRunner()
    return ContractTradingNodeSessionRunner()


def build_paper_trading_node_config(
    *,
    profile: ExecutionLaneProfile,
    command: ExecutionLaneCommand,
    plan: NautilusTradingNodeRuntimePlan,
    credential_values: dict[str, str],
) -> TradingNodeBuildResult:
    if profile.lane_mode != ExecutionLaneMode.PAPER or plan.runtime_environment != "sandbox":
        raise ValueError("paper TradingNode sessions require a sandbox paper runtime plan")
    if plan.readiness_status != "READY":
        raise ValueError(f"TradingNode runtime plan is not ready: {', '.join(plan.blocked_reasons)}")
    if not plan.credential_slot_ref:
        raise ValueError("paper TradingNode sessions require credential_slot_ref")
    if not credential_values:
        raise ValueError("credential_slot_ref did not resolve to credential values")

    from nautilus_trader.common import Environment
    from nautilus_trader.config import ImportableStrategyConfig, LiveExecEngineConfig, LiveRiskEngineConfig, LoggingConfig, TradingNodeConfig
    from nautilus_trader.model.identifiers import InstrumentId, TraderId

    strategy_config = ImportableStrategyConfig(
        strategy_path=PAPER_STRATEGY_PATH,
        config_path=PAPER_STRATEGY_CONFIG_PATH,
        config={
            "instrument_id": InstrumentId.from_str(str(command.order_intent.get("instrument_id", "UNKNOWN"))),
            "strategy_lineage_id": command.strategy_lineage_id,
            "strategy_version_id": command.strategy_version_id,
            "runtime_profile_id": profile.runtime_profile_id,
            "promotion_approval_id": command.promotion_approval_id,
            "execution_authority": False,
            "may_submit_order": False,
        },
    )
    data_clients, exec_clients, data_factories, exec_factories = _client_configs(
        profile=profile,
        command=command,
        credential_values=credential_values,
    )
    config = TradingNodeConfig(
        environment=Environment.SANDBOX,
        trader_id=TraderId(getattr(plan.config_contract, "trader_id", None) or f"BUILDER-{profile.project_id[:24]}"),
        exec_engine=LiveExecEngineConfig(
            reconciliation=True,
            reconciliation_lookback_mins=profile.reconciliation_lookback_mins,
            open_check_lookback_mins=max(60, profile.reconciliation_lookback_mins),
            position_check_lookback_mins=max(60, profile.reconciliation_lookback_mins),
            reconciliation_startup_delay_secs=profile.reconciliation_startup_delay_secs,
        ),
        risk_engine=LiveRiskEngineConfig(bypass=False),
        logging=LoggingConfig(log_level="ERROR", bypass_logging=True, log_colors=False, print_config=False),
        strategies=[strategy_config],
        data_clients=data_clients,
        exec_clients=exec_clients,
    )
    summary = {
        "config_type": type(config).__name__,
        "environment": "sandbox",
        "trader_id": str(config.trader_id),
        "reconciliation": bool(config.exec_engine.reconciliation),
        "reconciliation_lookback_mins": config.exec_engine.reconciliation_lookback_mins,
        "risk_engine_bypass": bool(config.risk_engine.bypass),
        "data_clients": {name: type(value).__name__ for name, value in data_clients.items()},
        "exec_clients": {name: type(value).__name__ for name, value in exec_clients.items()},
        "data_client_factories": {name: getattr(factory, "__name__", type(factory).__name__) for name, factory in data_factories.items()},
        "exec_client_factories": {name: getattr(factory, "__name__", type(factory).__name__) for name, factory in exec_factories.items()},
        "strategies": [PAPER_STRATEGY_PATH],
        "browser_credentials_allowed": False,
    }
    attached_strategy = {
        "strategy_path": PAPER_STRATEGY_PATH,
        "config_path": PAPER_STRATEGY_CONFIG_PATH,
        "strategy_lineage_id": command.strategy_lineage_id,
        "strategy_version_id": command.strategy_version_id,
        "promotion_approval_id": command.promotion_approval_id,
        "instrument_id": str(command.order_intent.get("instrument_id", "UNKNOWN")),
        "execution_authority": False,
        "may_submit_order": False,
    }
    return TradingNodeBuildResult(
        config=config,
        summary=summary,
        attached_strategy=attached_strategy,
        data_client_factories=data_factories,
        exec_client_factories=exec_factories,
    )


def build_execution_session_id(*, profile: ExecutionLaneProfile, command: ExecutionLaneCommand) -> str:
    return _session_id(profile=profile, command=command)


def build_session_from_runner_result(
    *,
    profile: ExecutionLaneProfile,
    command: ExecutionLaneCommand,
    plan: NautilusTradingNodeRuntimePlan,
    worker_id: str,
    credential_env_keys: list[str],
    build_result: TradingNodeBuildResult,
    runner_result: TradingNodeRunnerResult,
) -> ExecutionLaneSession:
    session_id = _session_id(profile=profile, command=command)
    started_at = _now_iso()
    events = [
        _event("INITIALIZED", "Execution session accepted by backend worker", session_id=session_id),
        _event("CONFIG_BUILT", "Nautilus TradingNodeConfig built with promoted strategy reference", session_id=session_id),
        *runner_result.lifecycle_events,
    ]
    return ExecutionLaneSession(
        session_id=session_id,
        command_id=command.command_id or "UNKNOWN",
        runtime_profile_id=profile.runtime_profile_id,
        tenant_id=profile.tenant_id,
        project_id=profile.project_id,
        lane_mode=profile.lane_mode,
        adapter_id=command.adapter_id,
        venue=command.venue,
        venue_account_id=command.venue_account_id,
        status=runner_result.status,
        lifecycle_status=runner_result.status,
        runner_mode=runner_result.runner_mode,
        worker_id=worker_id,
        started_at=started_at,
        runtime_environment=plan.runtime_environment,
        node_runtime=plan.node_runtime,
        runtime_label=plan.runtime_label,
        future_runtime=plan.future_runtime,
        strategy_lineage_id=command.strategy_lineage_id,
        strategy_version_id=command.strategy_version_id,
        trade_action_id=command.trade_action_id,
        promotion_approval_id=command.promotion_approval_id,
        credential_slot_ref=plan.credential_slot_ref or "UNBOUND",
        credential_env_keys=credential_env_keys,
        credential_values_resolved=True,
        tradingnode_config=build_result.summary if isinstance(build_result.summary, dict) else build_result.summary.model_dump(mode="json"),
        attached_strategy=build_result.attached_strategy,
        lifecycle_events=events,
        live_trading_enabled=False,
        execution_authority=False,
        may_submit_order=False,
    )


def stopped_session(session: ExecutionLaneSession, *, worker_id: str, stop_result: TradingNodeStopResult) -> ExecutionLaneSession:
    now = _now_iso()
    return session.model_copy(
        update={
            "status": stop_result.status,
            "lifecycle_status": stop_result.status,
            "worker_id": worker_id,
            "stopped_at": now,
            "disposed_at": now if stop_result.status == "DISPOSED" else None,
            "lifecycle_events": [*session.lifecycle_events, *stop_result.lifecycle_events],
        }
    )


def session_report_payload(session: ExecutionLaneSession) -> dict[str, Any]:
    payload = session.model_dump(mode="json")
    payload["secrets_storage"] = "local_env_file_ref"
    payload["browser_secret_echo"] = False
    return payload


def _client_configs(
    *,
    profile: ExecutionLaneProfile,
    command: ExecutionLaneCommand,
    credential_values: dict[str, str],
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any]]:
    from .adapter_config_builders import get_adapter_config_builder

    builder = get_adapter_config_builder(profile.adapter_id or "")
    return builder(profile=profile, command=command, credential_values=credential_values)


def _credential(values: dict[str, str], key: str) -> str | None:
    value = values.get(key)
    if value is None or str(value).strip() == "":
        return None
    return str(value)


def _truthy(value: object) -> bool:
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


def _session_id(*, profile: ExecutionLaneProfile, command: ExecutionLaneCommand) -> str:
    material = {
        "tenant_id": profile.tenant_id,
        "project_id": profile.project_id,
        "runtime_profile_id": profile.runtime_profile_id,
        "command_id": command.command_id,
        "strategy_version_id": command.strategy_version_id,
    }
    digest = hashlib.sha256(json.dumps(material, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()
    return f"exec_session_{digest[:16]}"


def _event(status: str, message: str, *, session_id: str) -> dict[str, Any]:
    return {"status": status, "message": message, "session_id": session_id, "timestamp": _now_iso()}


def _now_iso() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")
