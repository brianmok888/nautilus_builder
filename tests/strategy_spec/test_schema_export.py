"""Schema export tests — Segment 4."""
import json

from packages.strategy_spec.schema_export import export_v1_schema, export_v2_schema, export_all_schemas


class TestSchemaExport:
    def test_v1_schema_export(self) -> None:
        schema = export_v1_schema()
        assert "properties" in schema
        assert "schema_version" in json.dumps(schema)

    def test_v2_schema_export(self) -> None:
        schema = export_v2_schema()
        assert "properties" in schema
        assert "metadata" in json.dumps(schema)

    def test_all_schemas_include_v2(self) -> None:
        schemas = export_all_schemas()
        assert "v1" in schemas
        assert "v2" in schemas
        assert "feature_inputs" in json.dumps(schemas["v2"])

    def test_v2_schema_includes_risk_contract(self) -> None:
        schema = export_v2_schema()
        dumped = json.dumps(schema)
        assert "max_spread_bps" in dumped
        assert "max_position_notional" in dumped
