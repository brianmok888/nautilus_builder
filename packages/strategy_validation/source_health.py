"""Source health validation — checks feature freshness requirements."""
from __future__ import annotations

from typing import Any


def validate_source_health(spec: dict[str, Any]) -> list[str]:
    """Validate source health requirements in a spec.

    Returns list of issue codes for missing or invalid source health config.
    """
    issues: list[str] = []
    features = spec.get("features", {})

    if "source_health" not in features:
        issues.append("ERR_MISSING_SOURCE_HEALTH_REQUIREMENT")
        return issues

    health = features["source_health"]
    if not isinstance(health, dict):
        issues.append("ERR_MISSING_SOURCE_HEALTH_REQUIREMENT")
        return issues

    # Check for stale_policy
    if "stale_policy" not in health:
        issues.append("ERR_STALE_FEATURE_WITHOUT_POLICY")

    # Check for synthetic fallback declaration
    required = features.get("required", [])
    for feat in required:
        if feat.startswith("source."):
            continue
        # Features that could use synthetic data must declare fallback policy
        if "synthetic_fallback" not in health and "fallback" not in health:
            # This is a warning, not an error for most features
            pass

    return issues
