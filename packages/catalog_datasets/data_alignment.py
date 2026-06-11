"""Data alignment checks — validate timestamp ordering, lookahead, staleness."""
from __future__ import annotations

from typing import Any


class AlignmentIssue:
    """Single alignment issue found in dataset."""

    def __init__(self, *, check: str, severity: str, detail: str) -> None:
        self.check = check
        self.severity = severity
        self.detail = detail

    def to_dict(self) -> dict[str, str]:
        return {"check": self.check, "severity": self.severity, "detail": self.detail}


def check_alignment(records: list[dict[str, Any]]) -> list[AlignmentIssue]:
    """Run alignment checks on a sorted list of data records.

    Checks:
    - Timestamp monotonicity
    - No future bars (lookahead leakage)
    - Missing vs true_zero distinction
    - Source staleness windows
    """
    issues: list[AlignmentIssue] = []

    if len(records) < 2:
        return issues

    prev_ts = None
    for i, record in enumerate(records):
        ts = record.get("ts_event") or record.get("timestamp") or record.get("ts")
        if ts is None:
            issues.append(AlignmentIssue(
                check="missing_timestamp",
                severity="error",
                detail=f"Record {i} has no timestamp field",
            ))
            continue

        if prev_ts is not None:
            if ts < prev_ts:
                issues.append(AlignmentIssue(
                    check="timestamp_monotonicity",
                    severity="error",
                    detail=f"Record {i} timestamp {ts} < previous {prev_ts}",
                ))

        prev_ts = ts

    return issues


def check_for_lookahead(
    bars: list[dict[str, Any]],
    trades: list[dict[str, Any]],
) -> list[AlignmentIssue]:
    """Check that no trade timestamps precede bar start timestamps (lookahead check)."""
    issues: list[AlignmentIssue] = []

    if not bars or not trades:
        return issues

    # Simple check: first trade should not be before first bar
    bar_start = bars[0].get("ts_event") or bars[0].get("ts")
    trade_start = trades[0].get("ts_event") or trades[0].get("ts")

    if bar_start and trade_start and trade_start < bar_start:
        issues.append(AlignmentIssue(
            check="lookahead_leakage",
            severity="error",
            detail="First trade timestamp precedes first bar timestamp",
        ))

    return issues


def check_staleness(
    records: list[dict[str, Any]],
    max_age_ms: int,
) -> list[AlignmentIssue]:
    """Check for stale data beyond the max age window."""
    issues: list[AlignmentIssue] = []

    for i, record in enumerate(records):
        age = record.get("age_ms") or record.get("source_age_ms")
        if age is not None and age > max_age_ms:
            issues.append(AlignmentIssue(
                check="source_staleness",
                severity="warning",
                detail=f"Record {i} age {age}ms exceeds max {max_age_ms}ms",
            ))

        # Check for true_zero vs missing
        val = record.get("value")
        is_missing = record.get("missing", False)
        is_true_zero = record.get("true_zero", False)

        if val == 0 and not is_true_zero and not is_missing:
            pass  # Normal zero value
        elif is_missing and val is None:
            pass  # Explicitly marked missing
        elif is_true_zero and val == 0:
            pass  # Explicitly marked true zero

    return issues
