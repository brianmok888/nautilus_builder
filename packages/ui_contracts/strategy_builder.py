from __future__ import annotations

from pydantic import BaseModel, ConfigDict


STRATEGY_BUILDER_BLOCKS = [
    "EMA",
    "RSI",
    "crossed_above",
    "crossed_below",
    "gt",
    "lt",
]


class StrategyBuilderDraftState(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    indicators: list[dict[str, object]]
    entry: dict[str, object]
    exit: dict[str, object]
    validation_errors: list[str]


def serialize_strategy_builder_state(state: StrategyBuilderDraftState) -> dict[str, object]:
    return {
        "name": state.name,
        "status": "draft",
        "indicators": state.indicators,
        "entry": state.entry,
        "exit": state.exit,
    }
