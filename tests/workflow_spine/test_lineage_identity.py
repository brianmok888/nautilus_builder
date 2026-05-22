from packages.workflow_spine import StrategyIdentity, StrategyVersionIdentity


def test_strategy_identity_continuity_does_not_depend_on_display_name() -> None:
    original = StrategyIdentity(
        strategy_id="strat_001",
        strategy_lineage_id="lineage_alpha",
        display_name="EMA Pullback",
    )
    renamed = StrategyIdentity(
        strategy_id="strat_001",
        strategy_lineage_id="lineage_alpha",
        display_name="AI Improved RSI Pullback",
    )

    assert original.continuity_key == renamed.continuity_key
    assert original.display_name != renamed.display_name


def test_strategy_version_carries_ai_improvement_thread_ids() -> None:
    version = StrategyVersionIdentity(
        strategy_id="strat_001",
        strategy_lineage_id="lineage_alpha",
        strategy_version_id="sv_002",
        parent_version_id="sv_001",
        ai_thread_id="ai_thread_123",
        improvement_cycle_id="cycle_456",
        revision_reason="AI suggested lower RSI exit threshold after backtest",
    )

    assert version.continuity_key == "lineage_alpha"
    assert version.parent_version_id == "sv_001"
    assert version.ai_thread_id == "ai_thread_123"
    assert version.improvement_cycle_id == "cycle_456"


def test_imported_nd_strategy_gets_builder_lineage_and_source_ref() -> None:
    identity = StrategyIdentity(
        strategy_id="strat_imported_001",
        strategy_lineage_id="lineage_imported_nd_001",
        display_name="ND Mean Reversion",
        source_ref="nd://strategies/mean-reversion-live",
    )

    assert identity.continuity_key == "lineage_imported_nd_001"
    assert identity.source_ref == "nd://strategies/mean-reversion-live"
