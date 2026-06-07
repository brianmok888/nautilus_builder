from __future__ import annotations


from packages.lifecycle.models import LifecycleStage, StrategyVersionRecord
from packages.lifecycle.versioning import bump_stage_version, freeze_after_backtest_start


def test_draft_versions_are_editable() -> None:
    record = StrategyVersionRecord(
        version="0.1.0-draft.1",
        stage=LifecycleStage.DRAFT,
        is_frozen=False,
        validation_report_id=None,
        last_backtest_result_id=None,
    )

    assert record.is_editable is True


def test_backtest_used_testing_version_becomes_frozen() -> None:
    record = StrategyVersionRecord(
        version="0.2.0-test.1",
        stage=LifecycleStage.TESTING,
        is_frozen=False,
        validation_report_id="vr_001",
        last_backtest_result_id=None,
    )

    frozen = freeze_after_backtest_start(record)

    assert frozen.is_frozen is True
    assert frozen.is_editable is False


def test_beta_and_final_versions_are_never_editable() -> None:
    beta = StrategyVersionRecord(
        version="0.3.0-beta.1",
        stage=LifecycleStage.BETA,
        is_frozen=True,
        validation_report_id="vr_001",
        last_backtest_result_id="bt_001",
    )
    final = StrategyVersionRecord(
        version="1.0.0",
        stage=LifecycleStage.FINAL,
        is_frozen=True,
        validation_report_id="vr_001",
        last_backtest_result_id="bt_001",
    )

    assert beta.is_editable is False
    assert final.is_editable is False


def test_stage_version_bump_matches_stage_format() -> None:
    assert bump_stage_version(major=0, minor=1, patch=0, stage=LifecycleStage.DRAFT, iteration=2) == "0.1.0-draft.2"
    assert bump_stage_version(major=0, minor=2, patch=0, stage=LifecycleStage.TESTING, iteration=1) == "0.2.0-test.1"
    assert bump_stage_version(major=0, minor=3, patch=0, stage=LifecycleStage.BETA, iteration=1) == "0.3.0-beta.1"
    assert bump_stage_version(major=1, minor=0, patch=0, stage=LifecycleStage.FINAL, iteration=1) == "1.0.0"


def test_final_stage_does_not_grant_live_authority() -> None:
    record = StrategyVersionRecord(
        version="1.0.0",
        stage=LifecycleStage.FINAL,
        is_frozen=True,
        validation_report_id="vr_001",
        last_backtest_result_id="bt_001",
    )

    assert record.live_trading_authority is False
