"""Tests for strategy development guide cross-references (S15)."""
import importlib
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
GUIDE = REPO_ROOT / "doc" / "strategy_dev_guide.md"


class TestDevGuideReferences:
    """Verify all modules mentioned in the strategy dev guide exist."""

    def test_guide_exists(self):
        assert GUIDE.is_file(), "doc/strategy_dev_guide.md must exist"

    def test_strategy_spec_importable(self):
        mod = importlib.import_module("packages.strategy_spec.models")
        assert hasattr(mod, "StrategySpec")

    def test_strategy_validation_importable(self):
        mod = importlib.import_module("packages.strategy_validation.validators")
        assert hasattr(mod, "validate_strategy_spec")

    def test_strategy_compiler_importable(self):
        mod = importlib.import_module("packages.strategy_compiler.compiler")
        assert hasattr(mod, "compile_strategy_spec")

    def test_backtest_config_builder_importable(self):
        mod = importlib.import_module("packages.backtest_runner.config_builder")
        assert hasattr(mod, "build_backtest_config")

    def test_adapter_registry_importable(self):
        mod = importlib.import_module("packages.adapter_registry.service")
        assert hasattr(mod, "AdapterRegistryService")

    def test_guide_mentions_all_key_concepts(self):
        content = GUIDE.read_text()
        for concept in ["IndicatorSpec", "RuleBlock", "RiskBlock", "validate_strategy_spec",
                        "compile_strategy_spec", "build_backtest_config"]:
            assert concept in content, f"Guide must mention {concept}"

    def test_guide_mentions_safety(self):
        content = GUIDE.read_text().lower()
        assert "execution authority" in content
        assert "no raw code" in content or "forbidden" in content
        assert "draft" in content and "testing" in content and "final" in content

    def test_guide_mentions_demos(self):
        content = GUIDE.read_text()
        assert "demo_strategy_basic.py" in content
        assert "demo_strategy_backtest.py" in content
        assert "demo_adapter_discovery.py" in content
