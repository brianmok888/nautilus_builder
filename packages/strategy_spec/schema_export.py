"""Schema export for all StrategySpec families.

Exports JSON schemas for validation, documentation, and cross-system contracts.
Families: classic_v1, microstructure_v1
"""
from __future__ import annotations

import json
from pathlib import Path

from packages.strategy_spec.microstructure import StrategySpecMicrostructureV1
from packages.strategy_spec.models import StrategySpec as StrategySpecClassicV1


def export_classic_v1_schema() -> dict:
    """Export classic StrategySpec JSON schema."""
    return StrategySpecClassicV1.model_json_schema()


def export_microstructure_v1_schema() -> dict:
    """Export microstructure StrategySpec JSON schema."""
    return StrategySpecMicrostructureV1.model_json_schema()


def export_all_schemas() -> dict[str, dict]:
    """Export all schema families."""
    return {
        "classic_v1": export_classic_v1_schema(),
        "microstructure_v1": export_microstructure_v1_schema(),
    }


def write_schemas_to_dir(output_dir: Path) -> dict[str, Path]:
    """Write schema JSON files to a directory."""
    output_dir.mkdir(parents=True, exist_ok=True)
    paths = {}
    for family, schema in export_all_schemas().items():
        p = output_dir / f"strategy_spec.{family}.schema.json"
        p.write_text(json.dumps(schema, indent=2, sort_keys=True))
        paths[family] = p
    return paths


# Backward compat aliases for v1/v2 naming
export_v1_schema = export_classic_v1_schema
export_v2_schema = export_microstructure_v1_schema
