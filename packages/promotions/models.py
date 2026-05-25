from __future__ import annotations

from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, StrictStr


EvidenceRef = Annotated[StrictStr, Field(min_length=1)]


class PromotionEvidenceRefs(BaseModel):
    model_config = ConfigDict(extra="forbid")

    validation_report: EvidenceRef
    backtest_result: EvidenceRef
    no_lookahead_report: EvidenceRef
    gate_compatibility_report: EvidenceRef
    runtime_boundary_report: EvidenceRef
    risk_review: EvidenceRef


class PromotionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    strategy_version: str
    compile_hash: str
    profile: str
    may_submit_order: bool
    may_create_trade_action: bool
    gate_compatibility: bool
    manual_approval: bool
    evidence_refs: dict[str, str]
    evidence_checksums: dict[str, str] = Field(default_factory=dict)
