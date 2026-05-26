from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
WEB = ROOT / "apps" / "web"


def _read(path: str) -> str:
    return (WEB / path).read_text()


def test_dashboard_home_exposes_compact_command_center_workflow() -> None:
    dashboard = _read("components/dashboard/BuilderDashboard.tsx")

    for token in (
        "Command center",
        "Describe strategy",
        "AI → StrategySpec → Market data → Backtest → Review → Execution Lane",
        "Start drafting",
        "Continue to market setup",
        "Execution lane status",
    ):
        assert token in dashboard
    assert "submit_order" not in dashboard
    assert "TradeAction" not in dashboard


def test_ai_builder_section_guides_prompt_to_validated_draft_without_authority() -> None:
    ai = _read("components/ai-builder/AiStrategyCopilot.tsx")

    for token in (
        "Strategy intent",
        "Prompt examples",
        "Validation gate",
        "Generate StrategySpec",
        "Apply to Builder",
        "Backtest remains separate",
    ):
        assert token in ai
    assert 'type="password"' not in ai
    assert "api_key" not in ai.lower()


def test_strategy_editor_section_has_compact_editor_canvas_inspector_layout() -> None:
    workspace = _read("components/strategy-builder/StrategyBuilderWorkspace.tsx")

    for token in (
        "StrategySpec Editor",
        "Block canvas",
        "Inspector",
        "Spec preview",
        "Backend validation required",
        "compact-editor-layout",
    ):
        assert token in workspace


def test_market_dataset_section_surfaces_adapter_venue_instrument_and_catalog_guards() -> None:
    market = _read("components/market/MarketProfilePanel.tsx")

    for token in (
        "Market + Dataset Setup",
        "Adapter / Venue",
        "Instrument search",
        "Dataset profile",
        "Catalog guard",
        "Validate dataset profile",
    ):
        assert token in market
    assert "credential" not in market.lower()


def test_backtest_center_section_has_job_status_artifacts_and_observational_terminal() -> None:
    page = _read("app/backtests/[jobId]/page.tsx")
    client = _read("app/backtests/[jobId]/BacktestJobClient.tsx")
    launch_panel = _read("components/backtests/BacktestLaunchPanel.tsx")
    backtest_surface = page + client + launch_panel

    for token in (
        "Backtest Center",
        "Run configuration",
        "Job status",
        "Artifact manifest",
        "Observational terminal",
        "request cancel",
        "Run BacktestNode",
    ):
        assert token in backtest_surface
    assert "may_submit_order: false" in backtest_surface


def test_results_research_section_has_metrics_charts_and_research_placeholders() -> None:
    results = _read("components/results/ResultsDashboard.tsx")

    for token in (
        "Results / Research",
        "Metric cards",
        "Equity curve placeholder",
        "Drawdown placeholder",
        "Research notes",
        "chart library later",
    ):
        assert token in results
    assert "No execution authority" in results


def test_execution_config_section_keeps_feature_flags_read_only_and_secret_free() -> None:
    config = _read("components/config/ExecutionLaneFeaturePanel.tsx")

    for token in (
        "Execution Lane / Config",
        "Feature visibility matrix",
        "Venue binding",
        "Paper controls visibility only",
        "Live controls visibility only",
        "no browser credentials",
    ):
        assert token in config
    assert 'type="password"' not in config
    assert "api_key" not in config.lower()
