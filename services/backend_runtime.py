from __future__ import annotations

import argparse
import json
import sys

from packages.backend_runtime import verify_headless_backend_runtime


def main() -> None:
    parser = argparse.ArgumentParser(description="Verify Nautilus Builder headless backend runtime contracts.")
    parser.add_argument("--runtime-profile-id", default="rp_paper_001")
    parser.add_argument(
        "--require-nautilus",
        action="store_true",
        help="Exit non-zero when the pinned nautilus_trader runtime is not installed in this Python environment.",
    )
    args = parser.parse_args()

    report = verify_headless_backend_runtime(runtime_profile_id=args.runtime_profile_id)
    print(json.dumps(report.model_dump(mode="json"), sort_keys=True))
    if args.require_nautilus and not report.nautilus_trader.is_match:
        raise SystemExit(1)
    if not report.no_web_imports or not report.no_daedalus_imports:
        raise SystemExit(1)


if __name__ == "__main__":
    try:
        main()
    except BrokenPipeError:
        sys.exit(0)
