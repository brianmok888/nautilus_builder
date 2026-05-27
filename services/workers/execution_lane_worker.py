from __future__ import annotations

import argparse
import json

from packages.execution_lane import ExecutionLaneReport, ExecutionLaneService, ExecutionLaneSession
from packages.execution_lane.sessions import (
    TradingNodeSessionRunner,
    build_execution_session_id,
    build_paper_trading_node_config,
    build_session_from_runner_result,
    session_report_payload,
    stopped_session,
)


def run_execution_lane_worker_once(
    *,
    service: ExecutionLaneService,
    runtime_profile_id: str,
    worker_id: str = "execution_lane_worker",
) -> ExecutionLaneReport:
    """Claim one command and emit a TradingNode runtime-plan report.

    This worker seam is intentionally backend-only. It does not import strategy
    lane code, browser config, or live credentials, and it does not start a
    Nautilus node in contract tests.
    """

    command = service.claim_next(runtime_profile_id=runtime_profile_id, worker_id=worker_id)
    profile = service.get_profile(runtime_profile_id)
    plan = service.build_trading_node_runtime_plan(runtime_profile_id=runtime_profile_id, command_id=command.command_id)
    plan_payload = plan.model_dump(mode="json")
    plan_payload["risk_gate_status"] = "PASS" if plan.readiness_status == "READY" else "BLOCKED"
    plan_payload["credential_slot_bound"] = bool(plan.credential_slot_ref)
    plan_payload["credential_slot_ref"] = plan.credential_slot_ref
    plan_payload["secrets_storage"] = "local_env_file_ref" if plan.credential_slot_ref else "not_bound"
    return service.record_report(
        command_id=command.command_id,
        payload={
            "report_type": "tradingnode_runtime_plan",
            "venue": profile.venue or command.venue,
            "instrument_id": command.order_intent.get("instrument_id", "UNKNOWN"),
            "payload": plan_payload,
        },
    )



def start_execution_lane_paper_session(
    *,
    service: ExecutionLaneService,
    runtime_profile_id: str,
    command_id: str,
    worker_id: str = "execution_lane_worker",
    runner: TradingNodeSessionRunner | None = None,
) -> ExecutionLaneSession:
    """Claim an approved paper command and start a backend-owned TradingNode session."""

    command = service.get_command(command_id)
    profile = service.get_profile(runtime_profile_id)
    if command.runtime_profile_id != runtime_profile_id:
        raise ValueError("execution lane command runtime_profile_id does not match request")
    plan = service.build_trading_node_runtime_plan(runtime_profile_id=runtime_profile_id, command_id=command.command_id)
    if plan.lane_mode.value != "paper" or plan.runtime_environment != "sandbox":
        raise ValueError("paper session start requires a sandbox paper runtime plan")
    if plan.readiness_status != "READY":
        raise ValueError(f"execution lane runtime plan is not ready: {', '.join(plan.blocked_reasons)}")
    if not plan.credential_slot_ref:
        raise ValueError("paper session start requires credential_slot_ref")
    credential_values = service.resolve_credential_slot_values(plan.credential_slot_ref)
    build_result = build_paper_trading_node_config(
        profile=profile,
        command=command,
        plan=plan,
        credential_values=credential_values,
    )
    command = service.claim_command(command_id=command_id, worker_id=worker_id)
    session_id = build_execution_session_id(profile=profile, command=command)
    selected_runner = runner or service.session_runner
    runner_result = selected_runner.start(
        session_id=session_id,
        config=build_result.config,
        data_client_factories=build_result.data_client_factories,
        exec_client_factories=build_result.exec_client_factories,
    )
    session = build_session_from_runner_result(
        profile=profile,
        command=command,
        plan=plan,
        worker_id=worker_id,
        credential_env_keys=sorted(credential_values),
        build_result=build_result,
        runner_result=runner_result,
    )
    service.record_session(session)
    service.record_report(
        command_id=command.command_id,
        payload={
            "report_type": "tradingnode_paper_session_started",
            "venue": profile.venue or command.venue,
            "instrument_id": command.order_intent.get("instrument_id", "UNKNOWN"),
            "payload": session_report_payload(session),
        },
    )
    return session


def stop_execution_lane_session(
    *,
    service: ExecutionLaneService,
    session_id: str,
    worker_id: str = "execution_lane_worker",
    runner: TradingNodeSessionRunner | None = None,
) -> ExecutionLaneSession:
    """Stop and dispose a backend-owned TradingNode session."""

    session = service.get_session(session_id)
    selected_runner = runner or service.session_runner
    stop_result = selected_runner.stop(session_id=session_id)
    stopped = stopped_session(session, worker_id=worker_id, stop_result=stop_result)
    service.record_session(stopped)
    service.record_report(
        command_id=stopped.command_id,
        payload={
            "report_type": "tradingnode_paper_session_stopped",
            "venue": stopped.venue,
            "instrument_id": stopped.attached_strategy.get("instrument_id", "UNKNOWN"),
            "payload": session_report_payload(stopped),
        },
    )
    return stopped


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the standalone Nautilus Builder execution lane worker scaffold.")
    parser.add_argument("--runtime-profile-id", required=True)
    parser.add_argument("--worker-id", default="execution_lane_worker")
    args = parser.parse_args()

    service = ExecutionLaneService()
    try:
        report = run_execution_lane_worker_once(service=service, runtime_profile_id=args.runtime_profile_id, worker_id=args.worker_id)
        print(json.dumps(report.model_dump(mode="json"), sort_keys=True))
    except KeyError:
        snapshot = service.snapshot(runtime_profile_id=args.runtime_profile_id)
        snapshot["worker_id"] = args.worker_id
        snapshot["strategy_lane_coupled"] = False
        print(json.dumps(snapshot, sort_keys=True))


if __name__ == "__main__":
    main()
