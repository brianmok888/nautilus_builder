"""Static scan for forbidden references in generated strategy artifacts."""
from __future__ import annotations

import re
from dataclasses import dataclass, field


_FORBIDDEN_PATTERNS: list[tuple[str, str]] = [
    (r"\bsubmit_order\s*\(", "submit_order call"),
    (r"\bTradeAction\b", "TradeAction reference"),
    (r"\bapi_key\s*=\s*['\"]", "hardcoded api_key"),
    (r"\bsecret\s*=\s*['\"]", "hardcoded secret"),
    (r"\bapi_secret\s*=\s*['\"]", "hardcoded api_secret"),
    (r"\beval\s*\(", "eval() call"),
    (r"\bexec\s*\(", "exec() call"),
    (r"\bsubprocess\b", "subprocess reference"),
    (r"\bsocket\b", "socket reference"),
    (r"\brequests\.(get|post|put|delete)\s*\(", "HTTP request call"),
    (r"execution_authority\s*=\s*True", "execution_authority=True"),
]

# Patterns that must be present
_REQUIRED_PATTERNS: list[tuple[str, str]] = [
    (r"execution_authority\s*=\s*False", "execution_authority=False declaration"),
]


@dataclass(frozen=True)
class StaticScanResult:
    passed: bool
    violations: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


def scan_generated_artifact(code: str) -> StaticScanResult:
    """Scan generated strategy code for forbidden references.

    Returns a StaticScanResult with pass/fail and any violations found.
    """
    violations: list[str] = []

    for pattern, description in _FORBIDDEN_PATTERNS:
        if re.search(pattern, code):
            violations.append(f"forbidden: {description}")

    for pattern, description in _REQUIRED_PATTERNS:
        if not re.search(pattern, code):
            violations.append(f"missing required: {description}")

    return StaticScanResult(
        passed=len(violations) == 0,
        violations=violations,
    )
