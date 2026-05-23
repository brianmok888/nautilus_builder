from __future__ import annotations

from pydantic import BaseModel, ConfigDict


def _list_of_dicts(value: object) -> list[dict[str, object]]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, dict)]


def _dict_value(value: object) -> dict[str, object]:
    return dict(value) if isinstance(value, dict) else {}


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

    def inline_validation_messages(self) -> list[str]:
        return list(self.validation_errors)


def serialize_strategy_builder_state(state: StrategyBuilderDraftState) -> dict[str, object]:
    return {
        "name": state.name,
        "status": "draft",
        "indicators": state.indicators,
        "entry": state.entry,
        "exit": state.exit,
    }


def deserialize_strategy_spec(spec: dict[str, object]) -> StrategyBuilderDraftState:
    return StrategyBuilderDraftState(
        name=str(spec["name"]),
        indicators=_list_of_dicts(spec.get("indicators", [])),
        entry=_dict_value(spec.get("entry", {})),
        exit=_dict_value(spec.get("exit", {})),
        validation_errors=[],
    )
