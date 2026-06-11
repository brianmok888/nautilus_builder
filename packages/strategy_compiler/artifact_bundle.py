"""Artifact bundle — the complete compiled output of a strategy compilation.

Contains the manifest, normalized spec, compiled IR, and all sub-artifacts.
The entire bundle has a deterministic hash.

Hard rule: execution_authority is always False.
"""
from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from packages.builder_metadata.version import get_canonical_version
from packages.strategy_compiler.hashing import canonical_hash
from packages.strategy_compiler.ir import CompiledStrategyIR


class CompileArtifactManifest(BaseModel):
    """Full artifact manifest with all required hashes and metadata."""
    model_config = ConfigDict(extra="forbid")

    artifact_id: str
    builder_version: str = Field(default_factory=get_canonical_version)
    schema_version: str = "1.0"
    spec_hash: str
    validation_hash: str = ""
    feature_dependency_hash: str
    risk_contract_hash: str
    ir_hash: str
    replay_manifest_hash: str = ""
    artifact_hash: str = ""
    created_at_utc: str = ""
    profile: Literal["backtest", "signal_preview_only"] = "signal_preview_only"
    execution_authority: Literal[False] = False


class ArtifactManifest(BaseModel):
    """Legacy manifest kept for backward compatibility."""
    model_config = ConfigDict(extra="forbid")

    strategy_spec_hash: str
    compile_ir_hash: str
    feature_graph_hash: str
    risk_contract_hash: str


class ArtifactBundle(BaseModel):
    """Complete compiled artifact bundle with deterministic hashing."""
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


class FullArtifactBundle(BaseModel):
    """v2 artifact bundle with complete manifest, validation, and replay artifacts."""
    model_config = ConfigDict(extra="forbid")

    compile_manifest: CompileArtifactManifest
    normalized_spec: dict[str, Any]
    compiled_ir: CompiledStrategyIR
    feature_dependencies: dict[str, Any] = Field(default_factory=dict)
    risk_contract: dict[str, Any] = Field(default_factory=dict)
    validation_report: dict[str, Any] | None = None
    replay_manifest: dict[str, Any] | None = None

    def compute_bundle_hash(self) -> str:
        """Deterministic hash of the full bundle contents.

        Excludes created_at_utc and artifact_hash from the manifest
        to ensure reproducibility.
        """
        manifest_data = self.compile_manifest.model_dump()
        manifest_data.pop("created_at_utc", None)
        manifest_data.pop("artifact_hash", None)
        data = {
            "manifest": manifest_data,
            "normalized_spec": self.normalized_spec,
            "compiled_ir": self.compiled_ir.model_dump(),
            "feature_dependencies": self.feature_dependencies,
            "risk_contract": self.risk_contract,
        }
        return canonical_hash(data)

    @classmethod
    def build(
        cls,
        *,
        artifact_id: str,
        spec_hash: str,
        feature_dependency_hash: str,
        risk_contract_hash: str,
        ir_hash: str,
        normalized_spec: dict[str, Any],
        compiled_ir: CompiledStrategyIR,
        validation_hash: str = "",
        replay_manifest_hash: str = "",
        profile: Literal["backtest", "signal_preview_only"] = "signal_preview_only",
    ) -> "FullArtifactBundle":
        """Create a full artifact bundle, computing the bundle hash."""
        from datetime import datetime, timezone

        created_at = datetime.now(timezone.utc).isoformat()

        manifest = CompileArtifactManifest(
            artifact_id=artifact_id,
            spec_hash=spec_hash,
            validation_hash=validation_hash,
            feature_dependency_hash=feature_dependency_hash,
            risk_contract_hash=risk_contract_hash,
            ir_hash=ir_hash,
            replay_manifest_hash=replay_manifest_hash,
            created_at_utc=created_at,
            profile=profile,
        )

        bundle = cls(
            compile_manifest=manifest,
            normalized_spec=normalized_spec,
            compiled_ir=compiled_ir,
        )

        # Compute and set the artifact hash
        bundle_hash = bundle.compute_bundle_hash()
        bundle.compile_manifest.artifact_hash = bundle_hash

        return bundle
