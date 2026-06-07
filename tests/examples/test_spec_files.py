"""Tests for example JSON spec files in docs/examples/specs/ (Issue 1 & 4)."""
import json  # noqa: E402
import sys  # noqa: E402
from pathlib import Path  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
SPECS_DIR = REPO_ROOT / "docs" / "examples" / "specs"
EXAMPLES_DIR = REPO_ROOT / "docs" / "examples"

sys.path.insert(0, str(REPO_ROOT))

from packages.strategy_spec.models import StrategySpec  # noqa: E402


class TestExampleSpecFiles:
    """Verify example JSON spec files exist and are valid StrategySpecs."""

    def test_specs_directory_exists(self):
        assert SPECS_DIR.is_dir(), "docs/examples/specs/ must exist"

    def test_dual_ma_spec_exists(self):
        spec = SPECS_DIR / "dual_ma.json"
        assert spec.is_file(), "docs/examples/specs/dual_ma.json must exist"

    def test_rsi_reversal_spec_exists(self):
        spec = SPECS_DIR / "rsi_reversal.json"
        assert spec.is_file(), "docs/examples/specs/rsi_reversal.json must exist"

    def test_dual_ma_spec_valid_json(self):
        spec = SPECS_DIR / "dual_ma.json"
        data = json.loads(spec.read_text())
        assert isinstance(data, dict)

    def test_dual_ma_spec_validates_as_strategy_spec(self):
        spec = SPECS_DIR / "dual_ma.json"
        data = json.loads(spec.read_text())
        # Should not raise
        StrategySpec.model_validate(data)

    def test_rsi_reversal_spec_validates_as_strategy_spec(self):
        spec = SPECS_DIR / "rsi_reversal.json"
        data = json.loads(spec.read_text())
        StrategySpec.model_validate(data)

    def test_dual_ma_has_ema_indicators(self):
        spec = SPECS_DIR / "dual_ma.json"
        data = json.loads(spec.read_text())
        assert "ema_fast" in data.get("indicators", {})
        assert "ema_slow" in data.get("indicators", {})

    def test_rsi_reversal_has_rsi_indicator(self):
        spec = SPECS_DIR / "rsi_reversal.json"
        data = json.loads(spec.read_text())
        assert "rsi" in data.get("indicators", {})
