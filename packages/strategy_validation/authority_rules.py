"""Authority rules — ensure no live execution authority in spec."""
from __future__ import annotations

from typing import Any

FORBIDDEN_OUTPUT_MODES = {"live_execution", "execution_ready", "order_submission"}
FORBIDDEN_FIELDS = {
    "execution_authority", "may_submit_order", "live_trading_enabled",
    "auto_submit_orders", "submit_on_signal",
}


def check_authority(spec: dict[str, Any]) -> list[str]:
    """Check for forbidden authority fields and output modes."""
    issues: list[str] = []

    output = spec.get("output", {})
    mode = output.get("mode", "")
    if mode in FORBIDDEN_OUTPUT_MODES:
        issues.append("ERR_FORBIDDEN_OUTPUT_MODE")

    # Check top-level forbidden fields
    for field in FORBIDDEN_FIELDS:
        if field in spec:
            val = spec[field]
            if val is not False and val != "false":
                issues.append("ERR_LIVE_AUTHORITY_FIELD")

    return issues
