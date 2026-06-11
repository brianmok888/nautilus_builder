"""Compiled Strategy IR — deterministic intermediate representation."""
from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict


class CompiledStrategyIR(BaseModel):
    model_config = ConfigDict(extra="forbid")

    normalized_spec: dict[str, Any]
    compile_hash: str
    feature_graph_hash: str
    risk_contract_hash: str
    condition_count: int
    feature_count: int
    execution_authority: Literal[False] = False
