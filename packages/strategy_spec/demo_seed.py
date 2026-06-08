"""Seed 8 demo strategies covering every lifecycle status.

Strategies:
  1. demo_draft — Draft-only, no evidence
  2. demo_validation_failed — Validation failed
  3. demo_validated — Validated but not compiled
  4. demo_compiled — Compiled but no replay
  5. demo_replay_failed — Replay failed
  6. demo_replay_passed — Replay passed but no promotion
  7. demo_promotion_requested — Promotion requested
  8. demo_promotion_ready — Promotion ready / approved

Builder-only safety: no live execution, no TradeAction, no submit_order.
"""
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
from packages.auth import UserProjectContext
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

_VALIDATION_PASSED = ValidationFlags(bar_close_only=True, no_lookahead_required=True, requires_backtest_before_shadow=True, output_mode=OutputMode.SIGNAL_PREVIEW_ONLY)
_VALIDATION_FAILED = ValidationFlags(bar_close_only=True, no_lookahead_required=False, requires_backtest_before_shadow=True, output_mode=OutputMode.SIGNAL_PREVIEW_ONLY)

_DATA_RANGE = DataRange(start="2025-01-01T00:00:00Z", end="2025-06-01T00:00:00Z")

_DEMO_STRATEGIES: list[tuple[str, str, StrategyStatus, StrategyStage, ValidationFlags, CreatedFrom]] = [
    # 1. Draft-only — no evidence beyond creation
    ("demo_draft", "EMA RSI Crossover — Draft", StrategyStatus.DRAFT, StrategyStage.DRAFT, _VALIDATION_PASSED, CreatedFrom.AI_BUILDER),
    # 2. Validation failed — has false validation flag
    ("demo_validation_failed", "EMA RSI Crossover — Validation Failed", StrategyStatus.DRAFT, StrategyStage.DRAFT, _VALIDATION_FAILED, CreatedFrom.USER),
    # 3. Validated but not compiled
    ("demo_validated", "EMA RSI Crossover — Validated", StrategyStatus.VALIDATED, StrategyStage.TESTING, _VALIDATION_PASSED, CreatedFrom.USER),
    # 4. Compiled but no replay (backtested implies compile passed)
    ("demo_compiled", "EMA RSI Crossover — Compiled", StrategyStatus.BACKTESTED, StrategyStage.TESTING, _VALIDATION_PASSED, CreatedFrom.USER),
    # 5. Replay failed — backtested but will have a failed backtest job
    ("demo_replay_failed", "EMA RSI Crossover — Replay Failed", StrategyStatus.BACKTESTED, StrategyStage.TESTING, _VALIDATION_PASSED, CreatedFrom.USER),
    # 6. Replay passed but no promotion — backtested with succeeded job
    ("demo_replay_passed", "EMA RSI Crossover — Replay Passed", StrategyStatus.BACKTESTED, StrategyStage.TESTING, _VALIDATION_PASSED, CreatedFrom.USER),
    # 7. Promotion requested — approved status
    ("demo_promotion_requested", "EMA RSI Crossover — Promotion Requested", StrategyStatus.APPROVED, StrategyStage.BETA, _VALIDATION_PASSED, CreatedFrom.USER),
    # 8. Promotion ready — execution_ready status
    ("demo_promotion_ready", "EMA RSI Crossover — Promotion Ready", StrategyStatus.EXECUTION_READY, StrategyStage.FINAL, _VALIDATION_PASSED, CreatedFrom.USER),
]


def _make_spec(label: str, status: StrategyStatus, stage: StrategyStage, validation: ValidationFlags, created_from: CreatedFrom) -> StrategySpec:
    return StrategySpec(
        schema_version="1.0.0",
        version="0.1.0-draft.1" if stage == StrategyStage.DRAFT else "1.0.0",
        stage=stage,
        status=status,
        created_from=created_from,
        adapter_id="BINANCE_PERP",
        venue="BINANCE",
        instrument_id="BTCUSDT-PERP",
        bar_type="BTCUSDT-PERP.BINANCE-5-MINUTE-LAST-EXTERNAL",
        data_range=_DATA_RANGE,
        indicators={"ema_fast": _EMA_FAST, "ema_slow": _EMA_SLOW, "rsi": _RSI},
        rules={"long_entry": _LONG_ENTRY, "long_exit": _LONG_EXIT},
        risk=_RISK,
        validation=validation,
        provenance=Provenance(created_by=created_from),
    )


def seed_demo_strategies(
    repository: InMemoryStrategyRepository,
    *,
    context: UserProjectContext | None = None,
) -> None:
    """Populate the repository with one strategy per lifecycle status.

    Uses explicit IDs (demo_draft, demo_validated, …) so they don't collide
    with test-generated strategy_001…N IDs.

    This function is idempotent — calling it twice will not duplicate records
    because save_explicit overwrites existing entries.
    """
    for strategy_id, _label, status, stage, validation, created_from in _DEMO_STRATEGIES:
        spec = _make_spec(_label, status, stage, validation, created_from)
        repository.save_explicit(strategy_id, spec, context=context)
