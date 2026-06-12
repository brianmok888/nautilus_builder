"""Schema export tests — Segment 04 v5."""
import json

from packages.strategy_spec.schema_export import (
    export_all_schemas,
    export_classic_v1_schema,
    export_microstructure_v1_schema,
)


class TestSchemaExport:
    def test_classic_v1_schema_export(self) -> None:
        schema = export_classic_v1_schema()
        assert "properties" in schema
        assert "schema_version" in json.dumps(schema)

    def test_microstructure_v1_schema_export(self) -> None:
        schema = export_microstructure_v1_schema()
        assert "properties" in schema
        assert "execution_authority" in json.dumps(schema)

    def test_all_schemas_include_both_families(self) -> None:
        schemas = export_all_schemas()
        assert "classic_v1" in schemas
        assert "microstructure_v1" in schemas

    def test_microstructure_schema_includes_risk_contract(self) -> None:
        schema = export_microstructure_v1_schema()
        dumped = json.dumps(schema)
        assert "max_position_notional_usd" in dumped
        assert "max_loss_notional_usd" in dumped
        assert "max_hold_ms" in dumped
