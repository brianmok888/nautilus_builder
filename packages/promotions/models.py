from __future__ import annotations

from pydantic import BaseModel, ConfigDict


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
