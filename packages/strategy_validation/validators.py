from __future__ import annotations

from typing import Any

from pydantic import ValidationError

from packages.strategy_spec.models import StrategySpec

from .policy import FORBIDDEN_REFERENCES, RAW_CODE_PATTERNS
from .reports import ValidationReport


def _walk_strings(node: Any) -> list[str]:
    strings: list[str] = []
    if isinstance(node, str):
        strings.append(node)
    elif isinstance(node, dict):
        for key, value in node.items():
            strings.extend(_walk_strings(key))
            strings.extend(_walk_strings(value))
    elif isinstance(node, list):
        for item in node:
            strings.extend(_walk_strings(item))
    return strings


def validate_strategy_spec(payload: dict[str, Any]) -> ValidationReport:
    errors: list[str] = []

    raw_strings = _walk_strings(payload)
    lowered = [value.lower() for value in raw_strings]

    for forbidden, display_name in FORBIDDEN_REFERENCES.items():
        if any(forbidden in value for value in lowered):
            errors.append(f"forbidden execution reference detected: {display_name}")

    for pattern in sorted(RAW_CODE_PATTERNS):
        if any(pattern in value for value in lowered):
            errors.append(f"raw code pattern detected: {pattern}")

    risk = payload.get("risk")
    if not risk:
        errors.append("risk block missing")

    validation = payload.get("validation") or {}
    if validation.get("bar_close_only") is not True:
        errors.append("bar_close_only must be true")
    if validation.get("no_lookahead_required") is not True:
        errors.append("no_lookahead_required must be true")

    try:
        StrategySpec.model_validate(payload)
    except ValidationError as exc:
        for item in exc.errors():
            location = ".".join(str(part) for part in item.get("loc", ()))
            message = item.get("msg", "validation error")
            if location:
                errors.append(f"{location}: {message}")
            else:
                errors.append(message)

    deduped_errors = list(dict.fromkeys(errors))
    return ValidationReport(is_valid=not deduped_errors, errors=deduped_errors)
