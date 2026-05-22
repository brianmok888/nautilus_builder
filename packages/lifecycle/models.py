from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, ConfigDict


class LifecycleStage(str, Enum):
    DRAFT = "draft"
    TESTING = "testing"
    BETA = "beta"
    FINAL = "final"


class StrategyVersionRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    version: str
    stage: LifecycleStage
    is_frozen: bool
    validation_report_id: str | None
    last_backtest_result_id: str | None

    @property
    def is_editable(self) -> bool:
        return self.stage == LifecycleStage.DRAFT and not self.is_frozen

    @property
    def live_trading_authority(self) -> bool:
        return False


class PromotionEvidence(BaseModel):
    model_config = ConfigDict(extra="forbid")

    validation_passed: bool = False
    backtest_succeeded: bool = False
    no_lookahead_passed: bool = False
    shadow_evidence: bool = False
    gate_compatibility: bool = False
    manual_approval: bool = False
