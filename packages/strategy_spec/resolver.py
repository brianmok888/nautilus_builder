"""Strategy spec family resolver — unified parsing for classic and microstructure specs.

Routes payloads to the correct schema family based on schema_version discriminator.
"""
from __future__ import annotations

from typing import Any, Union

from packages.strategy_spec.microstructure import StrategySpecMicrostructureV1
from packages.strategy_spec.models import StrategySpec


StrategySpecFamily = Union[StrategySpec, StrategySpecMicrostructureV1]


def parse_strategy_spec(payload: dict[str, Any]) -> StrategySpecFamily:
    """Parse a strategy spec payload into the correct typed model.

    Uses schema_version discriminator:
    - "microstructure_v1" -> StrategySpecMicrostructureV1
    - anything else (including absent) -> StrategySpec (classic)

    Raises:
        pydantic.ValidationError: If the payload does not match any family.
    """
    schema_version = payload.get("schema_version", "")

    if schema_version == "microstructure_v1":
        return StrategySpecMicrostructureV1.model_validate(payload)

    return StrategySpec.model_validate(payload)


def get_spec_family_name(payload: dict[str, Any]) -> str:
    """Return the schema family name for a payload."""
    schema_version = payload.get("schema_version", "")
    if schema_version == "microstructure_v1":
        return "microstructure_v1"
    return "classic_v1"
