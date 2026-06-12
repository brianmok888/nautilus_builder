"""Evidence policy — required evidence types by promotion target level."""
from __future__ import annotations

from packages.promotions.gate import PromotionLevel


# Required evidence by promotion level (as specified in v2 Segment 09)
REQUIRED_EVIDENCE: dict[PromotionLevel, list[str]] = {
    PromotionLevel.VALIDATED: [
        "validation_report",
        "compile_artifact",
    ],
    PromotionLevel.COMPILED: [
        "validation_report",
        "compile_artifact",
    ],
    PromotionLevel.BACKTESTED_SYNTHETIC: [
        "validation_report",
        "compile_artifact",
        "replay_manifest",
        "backtest_result",
    ],
    PromotionLevel.BACKTESTED_CATALOG: [
        "validation_report",
        "compile_artifact",
        "replay_manifest",
        "real_dataset_backtest_result",
        "catalog_dataset_manifest",
    ],
    PromotionLevel.SHADOW_SIGNAL_PREVIEW: [
        "validation_report",
        "compile_artifact",
        "backtest_result",
    ],
    PromotionLevel.PAPER_READY: [
        "validation_report",
        "compile_artifact",
        "real_dataset_backtest_result",
        "data_tester_report",
        "manual_review",
    ],
    PromotionLevel.LIVE_CANDIDATE_EXTERNAL_ONLY: [
        "validation_report",
        "compile_artifact",
        "real_dataset_backtest_result",
        "data_tester_report",
        "exec_tester_report",
        "reconciliation_report",
        "manual_review",
    ],
}

# Canonical blocking reason codes
BLOCKING_REASONS = {
    "BLOCK_VALIDATION_FAILED",
    "BLOCK_COMPILE_ARTIFACT_MISSING",
    "BLOCK_EVIDENCE_MISSING",
    "BLOCK_EVIDENCE_UNVERIFIED",
    "BLOCK_SYNTHETIC_ONLY_REPLAY",
    "BLOCK_DATA_TESTER_REQUIRED",
    "BLOCK_EXEC_TESTER_REQUIRED",
    "BLOCK_RECONCILIATION_REQUIRED",
    "BLOCK_MANUAL_REVIEW_REQUIRED",
    "BLOCK_AUTHORITY_BOUNDARY_VIOLATION",
    "BLOCK_POLICY_CHECKSUM_MISMATCH",
}


def get_required_evidence(level: PromotionLevel) -> list[str]:
    """Return the list of required evidence types for a target level."""
    return REQUIRED_EVIDENCE.get(level, [])


# v5 promotion modes (safer naming)
V5_PROMOTION_MODES = {
    "shadow_only": PromotionLevel.SHADOW_SIGNAL_PREVIEW,
    "signal_preview_only": PromotionLevel.SHADOW_SIGNAL_PREVIEW,
    "paper_replay_candidate": PromotionLevel.PAPER_READY,
}

# Forbidden promotion modes — Builder must never grant these
FORBIDDEN_PROMOTION_MODES = {
    "live_trade_authority",
    "direct_trade_action_authority",
    "direct_submit_order_authority",
    "live_execution",
}

# v5 required evidence per mode
V5_REQUIRED_EVIDENCE: dict[str, list[str]] = {
    "shadow_only": [
        "strategy_spec",
        "validation_report",
        "compiler_ir",
        "risk_contract",
        "runtime_boundary_report",
    ],
    "signal_preview_only": [
        "strategy_spec",
        "validation_report",
        "compiler_ir",
        "risk_contract",
        "feature_dependency_graph",
        "replay_manifest_template",
        "manual_review",
    ],
    "paper_replay_candidate": [
        "strategy_spec",
        "validation_report",
        "compiler_ir",
        "risk_contract",
        "feature_dependency_graph",
        "replay_manifest_template",
        "catalog_dataset_manifest",
        "backtest_result",
        "no_lookahead_report",
        "gate_compatibility_report",
    ],
}


def get_v5_required_evidence(mode: str) -> list[str]:
    """Return required evidence for a v5 promotion mode."""
    if mode in FORBIDDEN_PROMOTION_MODES:
        raise ValueError(f"Forbidden promotion mode: {mode}")
    return V5_REQUIRED_EVIDENCE.get(mode, [])


def is_forbidden_mode(mode: str) -> bool:
    """Check if a promotion mode is forbidden for Builder."""
    return mode in FORBIDDEN_PROMOTION_MODES
