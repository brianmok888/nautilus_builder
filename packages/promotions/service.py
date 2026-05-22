from __future__ import annotations

from .models import PromotionRequest


class PromotionService:
    def create_shadow_request(
        self,
        *,
        strategy_version: str,
        compile_hash: str,
        gate_compatibility: bool,
    ) -> PromotionRequest:
        return PromotionRequest(
            strategy_version=strategy_version,
            compile_hash=compile_hash,
            profile="signal_preview_only",
            may_submit_order=False,
            may_create_trade_action=False,
            gate_compatibility=gate_compatibility,
            manual_approval=False,
            evidence_refs={
                "validation_report": "validation_report.md",
                "backtest_result": "backtest_result.json",
            },
        )

    def create_final_candidate(
        self,
        *,
        strategy_version: str,
        compile_hash: str,
        gate_compatibility: bool,
        manual_approval: bool,
    ) -> PromotionRequest:
        if not manual_approval:
            raise ValueError("manual approval is required")

        return PromotionRequest(
            strategy_version=strategy_version,
            compile_hash=compile_hash,
            profile="signal_preview_only",
            may_submit_order=False,
            may_create_trade_action=False,
            gate_compatibility=gate_compatibility,
            manual_approval=manual_approval,
            evidence_refs={
                "validation_report": "validation_report.md",
                "backtest_result": "backtest_result.json",
                "shadow_report": "shadow_report.md",
            },
        )
