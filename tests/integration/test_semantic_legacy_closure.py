from __future__ import annotations

from pathlib import Path


SOURCE_TRUTH_PATHS = [
    Path("packages/strategy_compiler/compiler.py"),
    Path("doc/nautilus_builder_hardguards.md"),
    Path("doc/nautilus_builder_implementation_plan.md"),
    Path("doc/nautilus_builder_implementation_prompts.md"),
]


def test_no_order_intent_wording_in_builder_no_order_source_truth() -> None:
    for path in SOURCE_TRUTH_PATHS:
        text = path.read_text()
        assert "backtest_order_intent" not in text
        assert "BacktestOrderIntent" not in text
