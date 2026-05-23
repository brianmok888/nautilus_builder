from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def test_strategy_spec_graph_helpers_are_limited_to_canonical_blocks() -> None:
    helper = (ROOT / "apps" / "web" / "lib" / "strategySpec.ts").read_text()

    assert "ALLOWED_STRATEGY_BLOCKS" in helper
    assert "EMA" in helper
    assert "RSI" in helper
    assert "submit_order" not in helper
    assert "graphToStrategySpec" in helper
    assert "strategySpecToGraph" in helper


def test_builder_workspace_mounts_palette_inspector_and_validation_surfaces() -> None:
    workspace = (ROOT / "apps" / "web" / "components" / "strategy-builder" / "StrategyBuilderWorkspace.tsx").read_text()

    assert "BlockPalette" in workspace
    assert "BlockInspector" in workspace
    assert "StrategyGraphCanvas" in workspace
    assert "StrategySpecEditor" in workspace
    assert "ValidationPanel" in workspace
    assert "backend validation" in workspace
