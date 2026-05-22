from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class AdapterProfile(BaseModel):
    model_config = ConfigDict(extra="forbid")

    adapter_id: str
    enabled: bool
    venue: str
    asset_class: str
    data_modes: list[str]
    execution_modes: dict[str, bool]
