from __future__ import annotations

import argparse
import json

from packages.execution_lane import ExecutionLaneService


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the standalone Nautilus Builder execution lane worker scaffold.")
    parser.add_argument("--runtime-profile-id", required=True)
    parser.add_argument("--worker-id", default="execution_lane_worker")
    args = parser.parse_args()

    service = ExecutionLaneService()
    snapshot = service.snapshot(runtime_profile_id=args.runtime_profile_id)
    snapshot["worker_id"] = args.worker_id
    snapshot["strategy_lane_coupled"] = False
    print(json.dumps(snapshot, sort_keys=True))


if __name__ == "__main__":
    main()
