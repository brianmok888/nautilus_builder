"""Schema export for StrategySpec v1 and v2.

Exports JSON schemas for validation, documentation, and cross-system contracts.
"""
from __future__ import annotations

import json
from pathlib import Path

from packages.strategy_spec.models import StrategySpec as StrategySpecV1
from packages.strategy_spec.models_v2 import StrategySpecV2


def export_v1_schema() -> dict:
    """Export StrategySpec v1 JSON schema."""
    return StrategySpecV1.model_json_schema()


def export_v2_schema() -> dict:
    """Export StrategySpec v2 JSON schema."""
    return StrategySpecV2.model_json_schema()


def export_all_schemas() -> dict[str, dict]:
    """Export all schema versions."""
    return {
        "v1": export_v1_schema(),
        "v2": export_v2_schema(),
    }


def write_schemas_to_dir(output_dir: Path) -> dict[str, Path]:
    """Write schema JSON files to a directory."""
    output_dir.mkdir(parents=True, exist_ok=True)
    paths = {}
    for version, schema in export_all_schemas().items():
        p = output_dir / f"strategy_spec_{version}_schema.json"
        p.write_text(json.dumps(schema, indent=2, sort_keys=True))
        paths[version] = p
    return paths
