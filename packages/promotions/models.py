from __future__ import annotations

from enum import Enum
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, StrictStr, field_validator


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


# --- Promotion mode validation ---


class AllowedPromotionMode(str, Enum):
    SHADOW_ONLY = "shadow_only"
    SIGNAL_PREVIEW_ONLY = "signal_preview_only"
    PAPER_REPLAY_CANDIDATE = "paper_replay_candidate"


_FORBIDDEN_MODES = {
    "live_trade_authority",
    "direct_trade_action_authority",
    "direct_submit_order_authority",
}

_ALLOWED_MODE_VALUES = {m.value for m in AllowedPromotionMode}


class ForbiddenPromotionMode(Exception):
    """Raised when a forbidden promotion mode is requested."""


def validate_promotion_mode(mode: str) -> AllowedPromotionMode:
    """Validate that the promotion mode is allowed for Builder.

    Raises ForbiddenPromotionMode for live execution authority modes.
    """
    if mode in _FORBIDDEN_MODES:
        raise ForbiddenPromotionMode(
            f"Promotion mode '{mode}' is forbidden from Builder. "
            f"Builder can only promote to: {', '.join(sorted(_ALLOWED_MODE_VALUES))}"
        )
    try:
        return AllowedPromotionMode(mode)
    except ValueError:
        raise ForbiddenPromotionMode(
            f"Unknown promotion mode '{mode}'. "
            f"Allowed: {', '.join(sorted(_ALLOWED_MODE_VALUES))}"
        ) from None


# --- Immutable promotion ledger entry ---


class PromotionLedgerEntry(BaseModel):
    """Immutable ledger entry linking all evidence hashes for a promotion."""
    model_config = ConfigDict(extra="forbid")

    strategy_id: str
    spec_version_id: str
    promotion_mode: str
    strategy_spec_hash: str
    compiler_hash: str
    policy_hash: str
    dataset_hash: str
    replay_report_hash: str
    artifact_hash: str
    artifact_uri: str
    requested_by: str
    approved_by: str | None = None
    execution_authority: Literal[False] = False

    @field_validator("promotion_mode")
    @classmethod
    def validate_mode_is_allowed(cls, v: str) -> str:
        validate_promotion_mode(v)
        return v
