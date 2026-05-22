from __future__ import annotations

from .models import LifecycleStage, StrategyVersionRecord


def bump_stage_version(*, major: int, minor: int, patch: int, stage: LifecycleStage, iteration: int) -> str:
    base = f"{major}.{minor}.{patch}"
    if stage == LifecycleStage.FINAL:
        return base

    stage_tag = {
        LifecycleStage.DRAFT: "draft",
        LifecycleStage.TESTING: "test",
        LifecycleStage.BETA: "beta",
    }[stage]
    return f"{base}-{stage_tag}.{iteration}"


def freeze_after_backtest_start(record: StrategyVersionRecord) -> StrategyVersionRecord:
    return record.model_copy(update={"is_frozen": True})
