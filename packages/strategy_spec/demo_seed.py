"""Seed 6 demo strategies covering every lifecycle status."""
from __future__ import annotations

from packages.strategy_spec.models import (
    CreatedFrom,
    DataRange,
    IndicatorInput,
    IndicatorSpec,
    IndicatorType,
    OutputMode,
    Provenance,
    RiskBlock,
    RuleBlock,
    RuleClause,
    StrategySpec,
    StrategyStage,
    StrategyStatus,
    ValidationFlags,
)
from packages.strategy_spec.repository import InMemoryStrategyRepository

_EMA_FAST = IndicatorSpec(type=IndicatorType.EMA, input=IndicatorInput.CLOSE, period=20)
_EMA_SLOW = IndicatorSpec(type=IndicatorType.EMA, input=IndicatorInput.CLOSE, period=50)
_RSI = IndicatorSpec(type=IndicatorType.RSI, input=IndicatorInput.CLOSE, period=14)

_LONG_ENTRY = RuleBlock(all=[
    RuleClause(crossed_above=["ema_fast", "ema_slow"]),
    RuleClause(gt=["rsi", 52]),
])
_LONG_EXIT = RuleBlock(any=[
    RuleClause(crossed_below=["ema_fast", "ema_slow"]),
    RuleClause(lt=["rsi", 45]),
])

_RISK = RiskBlock(position_size_pct=0.05, stop_loss_pct=0.012, take_profit_pct=0.024, max_hold_bars=48)
_VALIDATION = ValidationFlags(bar_close_only=True, no_lookahead_required=True, requires_backtest_before_shadow=True, output_mode=OutputMode.SIGNAL_PREVIEW_ONLY)
_DATA_RANGE = DataRange(start="2025-01-01T00:00:00Z", end="2025-06-01T00:00:00Z")

_DEMO_STRATEGIES: list[tuple[str, str, StrategyStatus, StrategyStage]] = [
    ("demo_draft", "EMA RSI Crossover — Draft", StrategyStatus.DRAFT, StrategyStage.DRAFT),
    ("demo_validated", "EMA RSI Crossover — Validated", StrategyStatus.VALIDATED, StrategyStage.TESTING),
    ("demo_backtested", "EMA RSI Crossover — Backtested", StrategyStatus.BACKTESTED, StrategyStage.TESTING),
    ("demo_approved", "EMA RSI Crossover — Approved", StrategyStatus.APPROVED, StrategyStage.BETA),
    ("demo_execution_ready", "EMA RSI Crossover — Execution Ready", StrategyStatus.EXECUTION_READY, StrategyStage.FINAL),
]


def _make_spec(label: str, status: StrategyStatus, stage: StrategyStage) -> StrategySpec:
    return StrategySpec(
        schema_version="1.0.0",
        version="0.1.0-draft.1" if stage == StrategyStage.DRAFT else "1.0.0",
        stage=stage,
        status=status,
        created_from=CreatedFrom.AI_BUILDER if stage == StrategyStage.DRAFT else CreatedFrom.USER,
        adapter_id="BINANCE_PERP",
        venue="BINANCE",
        instrument_id="BTCUSDT-PERP",
        bar_type="BTCUSDT-PERP.BINANCE-5-MINUTE-LAST-EXTERNAL",
        data_range=_DATA_RANGE,
        indicators={"ema_fast": _EMA_FAST, "ema_slow": _EMA_SLOW, "rsi": _RSI},
        rules={"long_entry": _LONG_ENTRY, "long_exit": _LONG_EXIT},
        risk=_RISK,
        validation=_VALIDATION,
        provenance=Provenance(created_by=CreatedFrom.USER),
    )


def seed_demo_strategies(repository: InMemoryStrategyRepository) -> None:
    """Populate the repository with one strategy per lifecycle status.

    Uses explicit IDs (demo_draft, demo_validated, …) so they don't collide
    with test-generated strategy_001…N IDs.
    """
    for strategy_id, _label, status, stage in _DEMO_STRATEGIES:
        spec = _make_spec(_label, status, stage)
        repository.save_explicit(strategy_id, spec)
