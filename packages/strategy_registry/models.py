from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, ConfigDict


class ExternalStrategyClassification(str, Enum):
    NATIVE_STRATEGY_SPEC = "NATIVE_STRATEGY_SPEC"
    DAEDALUS_SIGNAL_STRATEGY = "DAEDALUS_SIGNAL_STRATEGY"
    DAEDALUS_GATE_AWARE_STRATEGY = "DAEDALUS_GATE_AWARE_STRATEGY"
    NAUTILUS_RAW_STRATEGY = "NAUTILUS_RAW_STRATEGY"
    UNKNOWN_RAW_CODE = "UNKNOWN_RAW_CODE"
    UNSAFE_EXECUTION_STRATEGY = "UNSAFE_EXECUTION_STRATEGY"


class ExternalStrategyEntry(BaseModel):
    model_config = ConfigDict(extra="forbid")

    strategy_id: str
    source: str
    classification: ExternalStrategyClassification
    read_only: bool
    editable_in_ux: bool
    import_allowed: bool


class ImportedDraft(BaseModel):
    model_config = ConfigDict(extra="forbid")

    stage: str
    status: str
    version: str
    source_ref: str
    live_ready: bool


class StrategyModuleEntry(BaseModel):
    model_config = ConfigDict(extra="forbid")

    module_id: str
    strategy_class_path: str
    config_class_path: str
    input_kind: str = "strategy_spec"
    read_only: bool = True
    execution_authority: bool = False
    live_trading_enabled: bool = False
    credentials_required: bool = False
    resolution_mode: str = "metadata_only"
