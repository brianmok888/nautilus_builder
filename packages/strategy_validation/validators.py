from __future__ import annotations

import re
from datetime import datetime
from typing import Any

from pydantic import ValidationError

from packages.strategy_spec.models import RuleBlock, RuleClause, StrategySpec

from .policy import FORBIDDEN_REFERENCES, RAW_CODE_PATTERNS
from .reports import ValidationReport

_RULE_OPERATORS = ("crossed_above", "crossed_below", "gt", "lt", "gte", "lte", "eq")
_SAFE_PRICE_FIELDS = {"open", "high", "low", "close", "bid", "ask", "mid"}
_RAW_WORD_PATTERNS = {"eval", "exec", "import", "subprocess", "socket", "requests"}
_RAW_SUBSTRING_PATTERNS = RAW_CODE_PATTERNS - _RAW_WORD_PATTERNS


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

    for pattern in sorted(_RAW_SUBSTRING_PATTERNS):
        if any(pattern in value for value in lowered):
            errors.append(f"raw code pattern detected: {pattern}")

    for pattern in sorted(_RAW_WORD_PATTERNS):
        token = re.compile(rf"(?<![a-z0-9_]){re.escape(pattern)}(?![a-z0-9_])")
        if any(token.search(value) for value in lowered):
            errors.append(f"raw code pattern detected: {pattern}")

    risk = payload.get("risk")
    if not risk:
        errors.append("risk block missing")

    validation = payload.get("validation") or {}
    if validation.get("bar_close_only") is not True:
        errors.append("bar_close_only must be true")
    if validation.get("no_lookahead_required") is not True:
        errors.append("no_lookahead_required must be true")
    if validation.get("requires_backtest_before_shadow") is not True:
        errors.append("requires_backtest_before_shadow must be true")

    spec: StrategySpec | None = None
    try:
        spec = StrategySpec.model_validate(payload)
    except ValidationError as exc:
        for item in exc.errors():
            location = ".".join(str(part) for part in item.get("loc", ()))
            message = item.get("msg", "validation error")
            if location:
                errors.append(f"{location}: {message}")
            else:
                errors.append(message)

    if spec is not None:
        _validate_data_range(spec, errors)
        _validate_rule_references(spec, errors)

    deduped_errors = list(dict.fromkeys(errors))
    return ValidationReport(is_valid=not deduped_errors, errors=deduped_errors)


def _validate_data_range(spec: StrategySpec, errors: list[str]) -> None:
    start = _parse_iso_datetime(spec.data_range.start, "data_range.start", errors)
    end = _parse_iso_datetime(spec.data_range.end, "data_range.end", errors)
    if start is not None and end is not None and start >= end:
        errors.append("data_range.start must be before data_range.end")


def _parse_iso_datetime(value: str, field_name: str, errors: list[str]) -> datetime | None:
    normalized = value.replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(normalized)
    except ValueError:
        errors.append(f"{field_name} must be an ISO-8601 datetime")
        return None


def _validate_rule_references(spec: StrategySpec, errors: list[str]) -> None:
    known_refs = set(spec.indicators) | _SAFE_PRICE_FIELDS
    for rule_name, block in spec.rules.items():
        _validate_rule_block(rule_name, block, known_refs, errors)


def _validate_rule_block(rule_name: str, block: RuleBlock, known_refs: set[str], errors: list[str]) -> None:
    for block_name in ("all", "any"):
        clauses = getattr(block, block_name)
        if clauses is None:
            continue
        for index, clause in enumerate(clauses):
            _validate_rule_clause(
                location=f"rules.{rule_name}.{block_name}[{index}]",
                clause=clause,
                known_refs=known_refs,
                errors=errors,
            )


def _validate_rule_clause(*, location: str, clause: RuleClause, known_refs: set[str], errors: list[str]) -> None:
    for operator in _RULE_OPERATORS:
        operands = getattr(clause, operator)
        if operands is None:
            continue
        if len(operands) != 2:
            errors.append(f"{location}.{operator} must define exactly 2 operands")
            continue
        for operand in operands:
            if isinstance(operand, str) and operand not in known_refs:
                errors.append(f"{location}.{operator} operand {operand} is not a known indicator or field")
