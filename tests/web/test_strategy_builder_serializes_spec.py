from __future__ import annotations

from packages.ui_contracts.strategy_builder import (
    STRATEGY_BUILDER_BLOCKS,
    StrategyBuilderDraftState,
    serialize_strategy_builder_state,
)


def test_visual_edits_serialize_to_strategy_spec() -> None:
    state = StrategyBuilderDraftState(
        name="EMA RSI Pullback",
        indicators=[
            {"type": "EMA", "input": "close", "period": 20},
            {"type": "RSI", "input": "close", "period": 14},
        ],
        entry={"all": [{"crossed_above": ["close", "EMA_20"]}]},
        exit={"all": [{"gt": ["RSI_14", 70]}]},
        validation_errors=["risk block missing"],
    )

    spec = serialize_strategy_builder_state(state)

    assert spec["name"] == "EMA RSI Pullback"
    assert spec["entry"]["all"][0]["crossed_above"] == ["close", "EMA_20"]
    assert spec["status"] == "draft"


def test_unsupported_execution_blocks_are_unavailable() -> None:
    forbidden = {"submit_order", "TradeAction", "run_execution_lane"}

    assert forbidden.isdisjoint(set(STRATEGY_BUILDER_BLOCKS))


def test_validation_errors_are_surfaced_but_not_canonical_truth() -> None:
    state = StrategyBuilderDraftState(
        name="Test Draft",
        indicators=[],
        entry={"all": []},
        exit={"all": []},
        validation_errors=["adapter invalid"],
    )

    spec = serialize_strategy_builder_state(state)

    assert state.validation_errors == ["adapter invalid"]
    assert "validation_errors" not in spec
