"""Tests for promotion mode validation and immutable ledger constraints."""
from __future__ import annotations

import pytest

from packages.promotions.models import (
    AllowedPromotionMode,
    ForbiddenPromotionMode,
    PromotionLedgerEntry,
    validate_promotion_mode,
)


class TestPromotionModeValidation:
    def test_shadow_only_allowed(self):
        assert validate_promotion_mode("shadow_only") == AllowedPromotionMode.SHADOW_ONLY

    def test_signal_preview_only_allowed(self):
        assert validate_promotion_mode("signal_preview_only") == AllowedPromotionMode.SIGNAL_PREVIEW_ONLY

    def test_paper_replay_candidate_allowed(self):
        assert validate_promotion_mode("paper_replay_candidate") == AllowedPromotionMode.PAPER_REPLAY_CANDIDATE

    def test_live_trade_authority_forbidden(self):
        with pytest.raises(ForbiddenPromotionMode):
            validate_promotion_mode("live_trade_authority")

    def test_direct_trade_action_authority_forbidden(self):
        with pytest.raises(ForbiddenPromotionMode):
            validate_promotion_mode("direct_trade_action_authority")

    def test_direct_submit_order_authority_forbidden(self):
        with pytest.raises(ForbiddenPromotionMode):
            validate_promotion_mode("direct_submit_order_authority")

    def test_unknown_mode_forbidden(self):
        with pytest.raises(ForbiddenPromotionMode):
            validate_promotion_mode("unknown_mode")


class TestPromotionLedgerEntry:
    def test_ledger_entry_requires_all_hashes(self):
        entry = PromotionLedgerEntry(
            strategy_id="strat-001",
            spec_version_id="ver-001",
            promotion_mode="shadow_only",
            strategy_spec_hash="hash_spec",
            compiler_hash="hash_compiler",
            policy_hash="hash_policy",
            dataset_hash="hash_dataset",
            replay_report_hash="hash_replay",
            artifact_hash="hash_artifact",
            artifact_uri="artifact://builder/abc",
            requested_by="user-001",
        )
        assert entry.strategy_spec_hash == "hash_spec"
        assert entry.promotion_mode == "shadow_only"
        assert entry.execution_authority is False

    def test_ledger_entry_forbids_execution_authority(self):
        with pytest.raises(Exception):
            PromotionLedgerEntry(
                strategy_id="strat-001",
                spec_version_id="ver-001",
                promotion_mode="shadow_only",
                strategy_spec_hash="hash_spec",
                compiler_hash="hash_compiler",
                policy_hash="hash_policy",
                dataset_hash="hash_dataset",
                replay_report_hash="hash_replay",
                artifact_hash="hash_artifact",
                artifact_uri="artifact://builder/abc",
                requested_by="user-001",
                execution_authority=True,
            )

    def test_ledger_entry_forbids_live_promotion_mode(self):
        with pytest.raises(Exception):
            PromotionLedgerEntry(
                strategy_id="strat-001",
                spec_version_id="ver-001",
                promotion_mode="live_trade_authority",
                strategy_spec_hash="hash_spec",
                compiler_hash="hash_compiler",
                policy_hash="hash_policy",
                dataset_hash="hash_dataset",
                replay_report_hash="hash_replay",
                artifact_hash="hash_artifact",
                artifact_uri="artifact://builder/abc",
                requested_by="user-001",
            )
