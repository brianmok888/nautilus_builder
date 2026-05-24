from __future__ import annotations

FORBIDDEN_REFERENCES = {
    "submit_order": "submit_order",
    "modify_order": "modify_order",
    "cancel_order": "cancel_order",
    "close_position": "close_position",
    "set_leverage": "set_leverage",
    "place_order": "place_order",
    "broker_order": "broker_order",
    "exchange_order": "exchange_order",
    "api_key": "api_key",
    "secret_key": "secret_key",
    "credential": "credential",
    "tradeaction": "TradeAction",
}

RAW_CODE_PATTERNS = {
    "eval",
    "exec",
    "import",
    "subprocess",
    "socket",
    "requests",
    "open(",
    "os.",
    "sys.",
    "__import__",
}
