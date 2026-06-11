"""Capabilities model — defines permission scopes for Builder API users."""
from __future__ import annotations

from enum import Enum


class Capability(str, Enum):
    """Builder API capabilities for role-based access control."""
    STRATEGY_READ = "strategy:read"
    STRATEGY_WRITE = "strategy:write"
    VALIDATION_RUN = "validation:run"
    COMPILE_RUN = "compile:run"
    BACKTEST_RUN = "backtest:run"
    EVIDENCE_WRITE = "evidence:write"
    EVIDENCE_VERIFY = "evidence:verify"
    PROMOTION_REQUEST = "promotion:request"
    PROMOTION_APPROVE = "promotion:approve"
    ADMIN_READINESS = "admin:readiness"
    ADMIN_CONFIG = "admin:config"


# Default capabilities for a standard operator
DEFAULT_OPERATOR_CAPABILITIES = {
    Capability.STRATEGY_READ,
    Capability.STRATEGY_WRITE,
    Capability.VALIDATION_RUN,
    Capability.COMPILE_RUN,
    Capability.BACKTEST_RUN,
    Capability.EVIDENCE_WRITE,
    Capability.PROMOTION_REQUEST,
}

# Admin capabilities include all
ADMIN_CAPABILITIES = set(Capability)


def has_capability(user_capabilities: set[Capability], required: Capability) -> bool:
    """Check if a user has a specific capability."""
    return required in user_capabilities
