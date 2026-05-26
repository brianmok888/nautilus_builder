from __future__ import annotations

import argparse
import json

from packages.execution_lane import ExecutionLaneReport, ExecutionLaneService


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
