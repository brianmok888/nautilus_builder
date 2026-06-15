"""Redis Stream entry normalizer — missing != true_zero.

Safely converts Redis stream field values to Python types.
Missing fields (None or empty string) become None — never 0.
Explicit zero ("0", "0.0", 0, 0.0) stays zero.

This is critical for distinguishing "we never received this field" from
"the source explicitly sent zero."
"""

from __future__ import annotations

import json
from typing import Any


def parse_stream_fields(fields: dict[bytes, bytes]) -> dict[str, Any]:
    """Parse Redis stream entry hash into Python dict.

    Keys decoded from bytes. Values: JSON-parse if looks like JSON, else string.
    """
    result: dict[str, Any] = {}
    for key_b, val_b in fields.items():
        key = key_b.decode("utf-8") if isinstance(key_b, bytes) else str(key_b)
        val = val_b.decode("utf-8") if isinstance(val_b, bytes) else str(val_b)
        if val.startswith("{") or val.startswith("["):
            try:
                result[key] = json.loads(val)
            except (json.JSONDecodeError, ValueError):
                result[key] = val
        else:
            result[key] = val
    return result


def to_optional_float(value: Any) -> float | None:
    """Convert to float. None/empty → None (missing), not 0."""
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def to_optional_int(value: Any) -> int | None:
    """Convert to int. None/empty → None (missing), not 0."""
    if value is None or value == "":
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def to_optional_str(value: Any) -> str | None:
    """Convert to str. None/empty → None."""
    if value is None or (isinstance(value, str) and value.strip() == ""):
        return None
    return str(value) if value is not None else None


def is_explicit_zero(value: Any) -> bool:
    """Check if value is explicitly zero (not missing)."""
    if value is None or value == "":
        return False
    try:
        return float(value) == 0.0
    except (TypeError, ValueError):
        return False


def unwrap_payload(data: dict[str, Any]) -> dict[str, Any]:
    """Unwrap envelope payload if present.

    Supports three incoming shapes:
    1. Flat fields: {symbol: "BTC", price: "50000", ...}
    2. JSON field: {payload: '{"symbol": "BTC", ...}'}
    3. Envelope: {event_type: "market_trade", schema_version: "1", payload: '{"symbol": "BTC", ...}'}
    """
    payload_str = data.get("payload")
    if isinstance(payload_str, str) and (payload_str.startswith("{") or payload_str.startswith("[")):
        try:
            inner = json.loads(payload_str)
            if isinstance(inner, dict):
                return inner
        except (json.JSONDecodeError, ValueError):
            pass

    # If payload is already a dict (pre-parsed), use it
    if isinstance(payload_str, dict):
        return payload_str

    return data


def detect_force_liquidation(data: dict[str, Any]) -> tuple[bool, str | None]:
    """Detect force-liquidation flags from Redis data.

    Returns (is_liquidation, liq_side).
    Binance rule: SELL force order = LONG_LIQ, BUY force order = SHORT_LIQ.
    """
    flags = to_optional_str(data.get("flags", ""))
    if flags:
        if "long_liq" in flags.lower():
            return True, "long_liq"
        if "short_liq" in flags.lower():
            return True, "short_liq"

    force_order = to_optional_str(data.get("force_order", ""))
    side = to_optional_str(data.get("side", ""))
    if force_order and force_order.lower() in ("true", "1", "yes"):
        if side and side.upper() == "SELL":
            return True, "long_liq"
        if side and side.upper() == "BUY":
            return True, "short_liq"
        return True, None

    liq_side = to_optional_str(data.get("liq_side", ""))
    if liq_side and liq_side.lower() in ("long_liq", "short_liq"):
        return True, liq_side.lower()

    return False, None


def detect_trade_flags(data: dict[str, Any]) -> dict[str, bool]:
    """Detect trade flags from Redis data."""
    flags_str = to_optional_str(data.get("flags", ""))
    result = {
        "is_large_trade": False,
        "is_sweep": False,
    }
    if flags_str:
        flags_lower = flags_str.lower()
        result["is_large_trade"] = "large" in flags_lower
        result["is_sweep"] = "sweep" in flags_lower

    if to_optional_str(data.get("is_large_trade", "")) in ("true", "1", "yes"):
        result["is_large_trade"] = True
    if to_optional_str(data.get("is_sweep", "")) in ("true", "1", "yes"):
        result["is_sweep"] = True

    return result


def requires_fields(data: dict[str, Any], *field_names: str) -> bool:
    """Check if all required fields are present and non-None."""
    for name in field_names:
        if data.get(name) is None:
            return False
    return True
