from __future__ import annotations

from .models import AiDraftResult


class AiBuilderService:
    def generate_draft(
        self,
        prompt: str,
        *,
        force_invalid: bool = False,
        include_forbidden_execution: bool = False,
    ) -> AiDraftResult:
        lowered = prompt.lower()
        if include_forbidden_execution or "submit order" in lowered or "submit orders" in lowered:
            raise ValueError("forbidden execution request")

        spec = {
            "name": "EMA RSI Pullback Draft",
            "status": "draft",
            "stage": "draft",
            "output": "signal_preview_only",
            "indicators": [
                {"type": "EMA", "input": "close", "period": 20},
                {"type": "RSI", "input": "close", "period": 14},
            ],
            "entry": {"all": [{"crossed_above": ["close", "EMA_20"]}]},
            "exit": {"all": [{"gt": ["RSI_14", 70]}]},
            "risk": {"max_position_size": 1.0},
        }

        if force_invalid:
            spec.pop("risk", None)
            return AiDraftResult(
                spec=spec,
                accepted=False,
                validation_errors=["risk block missing"],
                explanation="Draft rejected until required Builder risk block is present.",
            )

        return AiDraftResult(
            spec=spec,
            accepted=True,
            validation_errors=[],
            explanation="Draft generated in advisory mode and kept in Draft lifecycle stage.",
        )
