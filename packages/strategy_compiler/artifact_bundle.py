"""Artifact bundle — the complete compiled output of a strategy compilation.

Contains the manifest, normalized spec, compiled IR, and all sub-artifacts.
The entire bundle has a deterministic hash.
"""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict

from packages.strategy_compiler.hashing import canonical_hash
from packages.strategy_compiler.ir import CompiledStrategyIR


class ArtifactManifest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    strategy_spec_hash: str
    compile_ir_hash: str
    feature_graph_hash: str
    risk_contract_hash: str


class ArtifactBundle(BaseModel):
    model_config = ConfigDict(extra="forbid")

    manifest: ArtifactManifest
    normalized_spec: dict[str, Any]
    compiled_ir: CompiledStrategyIR

    def compute_artifact_hash(self) -> str:
        """Deterministic hash of the entire artifact bundle."""
        data = {
            "manifest": self.manifest.model_dump(),
            "normalized_spec": self.normalized_spec,
            "compiled_ir": self.compiled_ir.model_dump(),
        }
        return canonical_hash(data)
