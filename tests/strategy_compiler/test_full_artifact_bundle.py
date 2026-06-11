"""Tests for FullArtifactBundle — deterministic hash, execution_authority=False."""
from __future__ import annotations

import pytest

from packages.strategy_compiler.artifact_bundle import (
    ArtifactManifest,
    CompileArtifactManifest,
    FullArtifactBundle,
)
from packages.strategy_compiler.ir import CompiledStrategyIR


def _make_ir(**overrides) -> CompiledStrategyIR:
    defaults = {
        "normalized_spec": {"test": True},
        "compile_hash": "a" * 64,
        "feature_graph_hash": "b" * 64,
        "risk_contract_hash": "c" * 64,
        "condition_count": 2,
        "feature_count": 3,
    }
    defaults.update(overrides)
    return CompiledStrategyIR(**defaults)


def _make_bundle(**ir_overrides) -> FullArtifactBundle:
    ir = _make_ir(**ir_overrides)
    return FullArtifactBundle.build(
        artifact_id="test_artifact_001",
        spec_hash="d" * 64,
        feature_dependency_hash=ir.feature_graph_hash,
        risk_contract_hash=ir.risk_contract_hash,
        ir_hash=ir.compile_hash,
        normalized_spec={"test": True},
        compiled_ir=ir,
    )


class TestFullArtifactBundle:
    def test_bundle_has_deterministic_hash(self):
        b1 = _make_bundle()
        b2 = _make_bundle()
        assert b1.compile_manifest.artifact_hash == b2.compile_manifest.artifact_hash

    def test_reordered_json_input_same_hash(self):
        """Same logical content, different key order -> same hash."""
        ir = _make_ir()
        b = FullArtifactBundle.build(
            artifact_id="test_002",
            spec_hash="d" * 64,
            feature_dependency_hash=ir.feature_graph_hash,
            risk_contract_hash=ir.risk_contract_hash,
            ir_hash=ir.compile_hash,
            normalized_spec={"z": 1, "a": 2},
            compiled_ir=ir,
        )
        b2 = FullArtifactBundle.build(
            artifact_id="test_002",
            spec_hash="d" * 64,
            feature_dependency_hash=ir.feature_graph_hash,
            risk_contract_hash=ir.risk_contract_hash,
            ir_hash=ir.compile_hash,
            normalized_spec={"a": 2, "z": 1},
            compiled_ir=ir,
        )
        assert b.compile_manifest.artifact_hash == b2.compile_manifest.artifact_hash

    def test_changed_risk_different_hash(self):
        b1 = _make_bundle(risk_contract_hash="c" * 64)
        b2 = _make_bundle(risk_contract_hash="e" * 64)
        assert b1.compile_manifest.artifact_hash != b2.compile_manifest.artifact_hash

    def test_execution_authority_always_false(self):
        b = _make_bundle()
        assert b.compile_manifest.execution_authority is False

    def test_execution_authority_cannot_be_true(self):
        with pytest.raises(Exception):
            CompileArtifactManifest(
                artifact_id="test",
                spec_hash="d" * 64,
                feature_dependency_hash="b" * 64,
                risk_contract_hash="c" * 64,
                ir_hash="a" * 64,
                execution_authority=True,
            )

    def test_unsupported_profile_fails(self):
        ir = _make_ir()
        with pytest.raises(Exception):
            FullArtifactBundle.build(
                artifact_id="test_bad",
                spec_hash="d" * 64,
                feature_dependency_hash=ir.feature_graph_hash,
                risk_contract_hash=ir.risk_contract_hash,
                ir_hash=ir.compile_hash,
                normalized_spec={"test": True},
                compiled_ir=ir,
                profile="live_execution",
            )

    def test_builder_version_populated(self):
        b = _make_bundle()
        assert b.compile_manifest.builder_version != ""
        assert b.compile_manifest.builder_version != "0.0.0-unknown"

    def test_artifact_id_set(self):
        b = _make_bundle()
        assert b.compile_manifest.artifact_id == "test_artifact_001"
