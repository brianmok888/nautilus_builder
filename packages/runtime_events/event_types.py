"""Runtime event types — structured event lineage for strategy lifecycle."""
from __future__ import annotations

from enum import Enum


class RuntimeEventType(str, Enum):
    STRATEGY_CREATED = "strategy.created"
    STRATEGY_VERSION_CREATED = "strategy.version_created"
    STRATEGY_VALIDATED = "strategy.validated"
    STRATEGY_COMPILE_REQUESTED = "strategy.compile_requested"
    STRATEGY_COMPILED = "strategy.compiled"
    BACKTEST_REQUESTED = "backtest.requested"
    BACKTEST_STARTED = "backtest.started"
    BACKTEST_COMPLETED = "backtest.completed"
    BACKTEST_FAILED = "backtest.failed"
    EVIDENCE_REGISTERED = "evidence.registered"
    EVIDENCE_VERIFIED = "evidence.verified"
    EVIDENCE_FAILED = "evidence.failed"
    PROMOTION_REQUESTED = "promotion.requested"
    PROMOTION_BLOCKED = "promotion.blocked"
    PROMOTION_APPROVED_SHADOW = "promotion.approved_shadow"
    PROMOTION_REJECTED = "promotion.rejected"
    RUNTIME_PLAN_VIEWED = "runtime_plan.viewed"
