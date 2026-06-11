"""Capabilities model — defines permission scopes for Builder API users.

v4 spec: capabilities cover strategy, validation, compile, backtest,
evidence, promotion, and admin operations. No live execution capabilities.
"""
from __future__ import annotations

from enum import Enum


class Capability(str, Enum):
    """Builder API capabilities for role-based access control."""
    # Strategy
    STRATEGY_CREATE = "strategy:create"
    STRATEGY_READ = "strategy:read"
    STRATEGY_UPDATE_DRAFT = "strategy:update_draft"
    # Validation
    STRATEGY_VALIDATE = "strategy:validate"
    # Compile
    STRATEGY_COMPILE = "strategy:compile"
    # Backtest
    BACKTEST_CREATE = "backtest:create"
    BACKTEST_CANCEL = "backtest:cancel"
    # Evidence
    EVIDENCE_CREATE = "evidence:create"
    EVIDENCE_VERIFY = "evidence:verify"
    # Promotion
    PROMOTION_REQUEST_SHADOW = "promotion:request_shadow"
    PROMOTION_REQUEST_SIGNAL_PREVIEW = "promotion:request_signal_preview"
    # Admin
    ADMIN_MANAGE_TOKENS = "admin:manage_tokens"
    ADMIN_READINESS = "admin:readiness"
    ADMIN_CONFIG = "admin:config"


# Role-based capability sets
VIEWER_CAPABILITIES = {
    Capability.STRATEGY_READ,
}

BUILDER_EDITOR_CAPABILITIES = {
    Capability.STRATEGY_CREATE,
    Capability.STRATEGY_READ,
    Capability.STRATEGY_UPDATE_DRAFT,
    Capability.STRATEGY_VALIDATE,
    Capability.STRATEGY_COMPILE,
}

BACKTEST_OPERATOR_CAPABILITIES = BUILDER_EDITOR_CAPABILITIES | {
    Capability.BACKTEST_CREATE,
    Capability.BACKTEST_CANCEL,
    Capability.EVIDENCE_CREATE,
    Capability.EVIDENCE_VERIFY,
}

PROMOTION_REQUESTER_CAPABILITIES = BACKTEST_OPERATOR_CAPABILITIES | {
    Capability.PROMOTION_REQUEST_SHADOW,
    Capability.PROMOTION_REQUEST_SIGNAL_PREVIEW,
}

ADMIN_CAPABILITIES = set(Capability)

# Default operator (most common role)
DEFAULT_OPERATOR_CAPABILITIES = PROMOTION_REQUESTER_CAPABILITIES


def has_capability(user_capabilities: set[Capability], required: Capability) -> bool:
    """Check if a user has a specific capability."""
    return required in user_capabilities


def capabilities_for_role(role: str) -> set[Capability]:
    """Return capabilities for a named role."""
    role_map = {
        "viewer": VIEWER_CAPABILITIES,
        "builder_editor": BUILDER_EDITOR_CAPABILITIES,
        "backtest_operator": BACKTEST_OPERATOR_CAPABILITIES,
        "promotion_requester": PROMOTION_REQUESTER_CAPABILITIES,
        "admin": ADMIN_CAPABILITIES,
    }
    return role_map.get(role, VIEWER_CAPABILITIES)
