from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class CompileArtifact(BaseModel):
    model_config = ConfigDict(extra="forbid")

    profile: str
    strategy_class: str
    output_mode: str
    execution_authority: bool
    spec_version: str
    adapter_id: str
    instrument_id: str
    compile_hash: str
