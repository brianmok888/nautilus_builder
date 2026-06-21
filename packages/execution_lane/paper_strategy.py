from __future__ import annotations

from nautilus_trader.config import StrategyConfig
from nautilus_trader.model.data import Bar, QuoteTick
from nautilus_trader.model.identifiers import InstrumentId
from nautilus_trader.trading.strategy import Strategy


class ExecutionLanePaperStrategyConfig(StrategyConfig, frozen=True):
    """No-order strategy attached to Builder paper TradingNode sessions.

    It carries the promoted StrategySpec lineage into Nautilus runtime config while
    deliberately keeping order authority disabled. The execution lane itself may
    later consume approved TradeAction contracts, but this strategy never calls
    submit_order.
    """
    instrument_id: InstrumentId
    strategy_lineage_id: str
    strategy_version_id: str
    runtime_profile_id: str
    promotion_approval_id: str | None = None
    execution_authority: bool = False
    may_submit_order: bool = False
    bar_type: str | None = None


class ExecutionLanePaperStrategy(Strategy):
    """Observational paper strategy shell for execution-lane lifecycle sessions."""

    profile = "paper_execution_observational"

    def __init__(self, config: ExecutionLanePaperStrategyConfig) -> None:
        super().__init__(config)
        self.instrument = None
        self.observed_quote_ticks = 0
        self.observed_bars = 0

    def on_start(self) -> None:
        self.instrument = self.cache.instrument(self.config.instrument_id)
        if self.instrument is None:
            self.log.warning(
                f"Instrument not found in cache for paper strategy: {self.config.instrument_id}; "
                "no subscriptions will be created until it is available."
            )
            return
        self.log.info(
            f"ExecutionLanePaperStrategy start: instrument={self.config.instrument_id} "
            f"bar_type={self.config.bar_type} lineage={self.config.strategy_lineage_id}"
        )
        if self.config.bar_type:
            # Warmup: request historical bars before subscribing so any future
            # indicator logic has a populated buffer (NautilusTrader convention).
            self.request_bars(bar_type=self.config.bar_type)
            self.subscribe_bars(bar_type=self.config.bar_type)
        else:
            self.subscribe_quote_ticks(instrument_id=self.config.instrument_id)

    def on_stop(self) -> None:
        self.log.info(
            f"ExecutionLanePaperStrategy stop: instrument={self.config.instrument_id} "
            f"bar_type={self.config.bar_type} lineage={self.config.strategy_lineage_id}"
        )
        if self.config.bar_type:
            self.unsubscribe_bars(bar_type=self.config.bar_type)
        else:
            self.unsubscribe_quote_ticks(instrument_id=self.config.instrument_id)

    def on_reset(self) -> None:
        self.log.info(
            f"ExecutionLanePaperStrategy reset: instrument={self.config.instrument_id} "
            f"lineage={self.config.strategy_lineage_id}"
        )
        self.instrument = None
        self.observed_quote_ticks = 0
        self.observed_bars = 0

    def on_quote_tick(self, tick: QuoteTick) -> None:
        self.observed_quote_ticks += 1

    def on_bar(self, bar: Bar) -> None:
        self.observed_bars += 1
