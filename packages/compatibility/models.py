"""Compatibility models — Segment N v4.

Explicit versioned contracts between Builder and Nautilus-Daedalus/NautilusTrader.
"""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict


class CompatibilityContract(BaseModel):
    """Compatibility contract between Builder and external systems."""
    model_config = ConfigDict(extra="forbid")

    nautilus_trader_version_pin: str
    python_version: str
    strategy_spec_schema_version: str
    feature_schema_version: str
    dataset_manifest_schema_version: str
    compiled_ir_schema_version: str
    promotion_contract_version: str
    allowed_output_modes: list[Literal["signal_preview_only", "shadow_observation"]] = [
        "signal_preview_only",
        "shadow_observation",
    ]
    forbidden_outputs: list[str] = [
        "TradeAction",
        "submit_order",
        "live_order_request",
    ]


class CompatibilityMatrix(BaseModel):
    """Full compatibility matrix for Builder integration."""
    model_config = ConfigDict(extra="forbid")

    builder_version: str
    contract: CompatibilityContract
    checked_at: str

    def is_compatible(self, nt_version: str) -> bool:
        """Check if a given NT version is compatible."""
        return nt_version == self.contract.nautilus_trader_version_pin

    def is_forbidden(self, output_type: str) -> bool:
        """Check if an output type is forbidden."""
        return output_type in self.contract.forbidden_outputs
