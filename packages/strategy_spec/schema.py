from __future__ import annotations

import json
from pathlib import Path

from .models import StrategySpec


def export_strategy_spec_schema(output_path: str | Path) -> Path:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    schema = StrategySpec.model_json_schema()
    path.write_text(json.dumps(schema, indent=2) + "\n")
    return path
