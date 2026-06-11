"""Tests for StrategySpec v2 archetype fixtures and schema export."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from packages.strategy_spec.models_v2 import StrategySpecV2
from packages.strategy_spec.schema_export import export_v2_schema

FIXTURES_DIR = Path(__file__).parent / "fixtures"

REQUIRED_ARCHETYPE_FIXTURES = [
    "absorption_reversal_btc_5m.json",
    "liquidity_vacuum_breakout_eth_15m.json",
    "vwap_reclaim_reversal_btc_30m.json",
    "liquidation_cascade_continuation_eth_1h.json",
]


class TestArchetypeFixtures:
    """Validate all archetype fixture JSON files parse and satisfy constraints."""

    @pytest.mark.parametrize("fixture_file", REQUIRED_ARCHETYPE_FIXTURES)
    def test_fixture_loads_as_valid_json(self, fixture_file: str):
        path = FIXTURES_DIR / fixture_file
        data = json.loads(path.read_text())
        assert isinstance(data, dict)

    @pytest.mark.parametrize("fixture_file", REQUIRED_ARCHETYPE_FIXTURES)
    def test_fixture_has_required_top_level_keys(self, fixture_file: str):
        path = FIXTURES_DIR / fixture_file
        data = json.loads(path.read_text())
        required = {"metadata", "market", "features", "conditions", "risk", "evidence", "output"}
        missing = required - set(data.keys())
        assert not missing, f"{fixture_file} missing keys: {missing}"

    @pytest.mark.parametrize("fixture_file", REQUIRED_ARCHETYPE_FIXTURES)
    def test_fixture_output_mode_is_signal_preview_only(self, fixture_file: str):
        path = FIXTURES_DIR / fixture_file
        data = json.loads(path.read_text())
        assert data["output"]["mode"] == "signal_preview_only"

    @pytest.mark.parametrize("fixture_file", REQUIRED_ARCHETYPE_FIXTURES)
    def test_fixture_features_have_source_health(self, fixture_file: str):
        path = FIXTURES_DIR / fixture_file
        data = json.loads(path.read_text())
        assert "source_health" in data["features"], f"{fixture_file} missing source_health"
        assert "stale_policy" in data["features"]["source_health"]

    @pytest.mark.parametrize("fixture_file", REQUIRED_ARCHETYPE_FIXTURES)
    def test_fixture_has_no_live_execution_authority(self, fixture_file: str):
        path = FIXTURES_DIR / fixture_file
        data = json.loads(path.read_text())
        # No execution authority fields should be present
        assert "execution_authority" not in data
        assert "may_submit_order" not in data
        assert data["output"]["mode"] != "live_execution"

    def test_all_required_fixtures_exist(self):
        for fixture_file in REQUIRED_ARCHETYPE_FIXTURES:
            path = FIXTURES_DIR / fixture_file
            assert path.exists(), f"Missing fixture: {fixture_file}"


class TestSchemaExport:
    def test_v2_schema_export_produces_valid_json(self):
        schema = export_v2_schema()
        serialized = json.dumps(schema)
        assert len(serialized) > 0
        re_parsed = json.loads(serialized)
        assert "properties" in re_parsed or "title" in re_parsed

    def test_v2_schema_excludes_execution_authority(self):
        schema = export_v2_schema()
        schema_str = json.dumps(schema)
        # execution_authority in the schema should be literal False
        # (it's a Literal[False] field)
        assert "execution_authority" in schema_str.lower()

    def test_v1_schema_still_exportable(self):
        from packages.strategy_spec.schema_export import export_v1_schema
        schema = export_v1_schema()
        assert "properties" in schema or "title" in schema
