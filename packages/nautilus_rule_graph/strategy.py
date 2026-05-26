from __future__ import annotations

from typing import Any

from packages.nautilus_rule_graph.evaluator import RuleGraphEvaluator

from nautilus_trader.config import StrategyConfig
from nautilus_trader.model.data import QuoteTick
from nautilus_trader.model.identifiers import InstrumentId
from nautilus_trader.trading.strategy import Strategy


class RuleGraphBacktestStrategyConfig(StrategyConfig, frozen=True):
    instrument_id: InstrumentId
    strategy_spec: dict[str, Any]
    compile_hash: str


class RuleGraphBacktestStrategy(Strategy):
    """No-order StrategySpec replay strategy for Builder backtest evidence."""

    profile = "backtest"

    def __init__(self, config: RuleGraphBacktestStrategyConfig) -> None:
        super().__init__(config)
        self.instrument = None
        self.observed_quote_ticks = 0
        self.rule_graph_evaluator = RuleGraphEvaluator.from_payload(config.strategy_spec)
        self.rule_graph_evidence: dict[str, object] = self.rule_graph_evaluator.evidence()

    def on_start(self) -> None:
        self.instrument = self.cache.instrument(self.config.instrument_id)
        if self.instrument is None:
            self.log.error(f"Could not find instrument for {self.config.instrument_id}")
            self.stop()
            return
        self.subscribe_quote_ticks(instrument_id=self.config.instrument_id)

    def on_quote_tick(self, tick: QuoteTick) -> None:
        self.observed_quote_ticks += 1
        self.rule_graph_evidence = self.rule_graph_evaluator.update_quote_tick(tick)


class RuleGraphSignalStrategy:
    profile = "signal_preview_only"
