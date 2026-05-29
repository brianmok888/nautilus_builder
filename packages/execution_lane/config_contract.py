from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class DataClientEntry(BaseModel):
    model_config = ConfigDict(extra="forbid")
    adapter_id: str | None = None
    venue_account_id: str | None = None
    credential_slot_ref: str | None = None
    browser_credentials_allowed: Literal[False] = False


class ExecClientEntry(BaseModel):
    model_config = ConfigDict(extra="forbid")
    adapter_id: str | None = None
    venue_account_id: str | None = None
    credential_slot_ref: str | None = None
    paper_mode: bool = False
    live_authority: bool = False
    browser_credentials_allowed: Literal[False] = False


class ExecEngineConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    reconciliation: bool = True
    reconciliation_lookback_mins: int = Field(default=60, ge=60)
    reconciliation_startup_delay_secs: float = Field(default=10.0, ge=10.0)
    open_check_lookback_mins: int = Field(default=60, ge=60)
    position_check_lookback_mins: int = Field(default=60, ge=60)


class RiskEngineConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    bypass: Literal[False] = False
    risk_profile_id: str | None = None


class TradingNodeConfigContract(BaseModel):
    model_config = ConfigDict(extra="forbid")
    runtime_note: str = ""
    trader_id: str = Field(min_length=1)
    environment: Literal["sandbox", "live"]
    data_clients: dict[str, DataClientEntry]
    exec_clients: dict[str, ExecClientEntry]
    exec_engine: ExecEngineConfig
    risk_engine: RiskEngineConfig
