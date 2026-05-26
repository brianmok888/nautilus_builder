from __future__ import annotations

from tests.strategy_spec.test_schema_valid import make_valid_spec
from packages.nautilus_rule_graph.evaluator import evaluate_strategy_spec_prices


def test_rule_graph_evaluator_derives_no_order_signal_observations_from_strategy_spec() -> None:
    spec = make_valid_spec()
    spec["indicators"]["ema_fast"]["period"] = 1
    spec["indicators"]["ema_slow"]["period"] = 3
    spec["rules"]["long_entry"] = {"all": [{"crossed_above": ["ema_fast", "ema_slow"]}]}
    spec["rules"]["long_exit"] = {"any": [{"crossed_below": ["ema_fast", "ema_slow"]}]}

    evidence = evaluate_strategy_spec_prices(spec, [10.0, 9.0, 12.0, 14.0])

    assert evidence["strategy_logic_evaluated"] is True
    assert evidence["signal_observation_count"] == 4
    assert evidence["rule_evaluation_count"] >= 8
    assert evidence["rules"]["long_entry"]["true_count"] >= 1
    assert evidence["live_trading_enabled"] is False
    assert evidence["execution_authority"] is False
    assert evidence["may_submit_order"] is False
    assert evidence["order_intent_count"] == 0
