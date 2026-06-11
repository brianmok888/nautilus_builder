"""Validation report models — structured issue codes with remediation."""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class ValidationIssue(BaseModel):
    """Single validation issue with structured code."""
    model_config = ConfigDict(extra="forbid")

    severity: Literal["error", "warning", "info"]
    code: str
    path: str = ""
    message: str
    blocking: bool = True
    remediation: str | None = None


class ValidationReport(BaseModel):
    """Detailed validation report with structured issues."""
    model_config = ConfigDict(extra="forbid")

    is_valid: bool
    blocking_issue_count: int = 0
    issues: list[ValidationIssue] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    normalized_spec_hash: str = ""
    feature_dependency_hash: str = ""
    schema_version: str = ""

    @classmethod
    def from_issues(
        cls,
        issues: list[ValidationIssue],
        *,
        spec_hash: str = "",
        feature_hash: str = "",
        schema_version: str = "",
    ) -> "ValidationReport":
        """Create a report from a list of issues."""
        blocking = [i for i in issues if i.blocking]
        errors_str = [f"[{i.code}] {i.message}" for i in issues if i.severity == "error"]
        warnings_str = [f"[{i.code}] {i.message}" for i in issues if i.severity == "warning"]
        return cls(
            is_valid=len(blocking) == 0,
            blocking_issue_count=len(blocking),
            issues=issues,
            errors=errors_str,
            warnings=warnings_str,
            normalized_spec_hash=spec_hash,
            feature_dependency_hash=feature_hash,
            schema_version=schema_version,
        )


# Canonical error codes
KNOWN_ERROR_CODES = {
    "ERR_UNKNOWN_FEATURE_REF",
    "ERR_FORBIDDEN_OUTPUT_MODE",
    "ERR_LIVE_AUTHORITY_FIELD",
    "ERR_MISSING_SOURCE_HEALTH_REQUIREMENT",
    "ERR_STALE_FEATURE_WITHOUT_POLICY",
    "ERR_SYNTHETIC_FALLBACK_UNDECLARED",
    "ERR_RISK_LIMIT_MISSING",
    "ERR_SPREAD_LIMIT_MISSING",
    "ERR_SLIPPAGE_LIMIT_MISSING",
    "ERR_DEPTH_LIMIT_MISSING",
    "ERR_REPLAY_DATASET_REQUIRED",
    "ERR_EVIDENCE_TYPE_UNKNOWN",
}

KNOWN_WARNING_CODES = {
    "WARN_OPTIONAL_FEATURE_MISSING",
    "WARN_CLASSIC_INDICATOR_ONLY_STRATEGY",
}
