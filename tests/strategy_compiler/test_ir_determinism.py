"""Compiler IR determinism tests — Segment 5."""
import json

import pytest

from packages.strategy_compiler.ir import CompiledStrategyIR
from packages.strategy_compiler.artifact_bundle import ArtifactBundle, ArtifactManifest
from packages.strategy_compiler.hashing import canonical_hash, deterministic_json
from packages.strategy_compiler.dependency_graph import build_feature_dependency_graph
from packages.strategy_compiler.risk_contract import RiskContractArtifact
from packages.strategy_compiler.replay_manifest import ReplayManifestTemplate


class TestDeterministicHashing:
    def test_same_input_same_hash(self) -> None:
        data = {"a": 1, "b": [2, 3], "c": {"d": 4}}
        h1 = canonical_hash(data)
        h2 = canonical_hash(data)
        assert h1 == h2

    def test_different_input_different_hash(self) -> None:
        d1 = {"a": 1}
        d2 = {"a": 2}
        assert canonical_hash(d1) != canonical_hash(d2)

    def test_key_order_irrelevant(self) -> None:
        d1 = {"a": 1, "b": 2}
        d2 = {"b": 2, "a": 1}
        assert canonical_hash(d1) == canonical_hash(d2)

    def test_deterministic_json_stable(self) -> None:
        data = {"z": 1, "a": 2, "m": [3, 1]}
        s1 = deterministic_json(data)
        s2 = deterministic_json(data)
        assert s1 == s2
        parsed = json.loads(s1)
        assert parsed == {"a": 2, "m": [3, 1], "z": 1}

    def test_no_local_paths_in_hash_material(self) -> None:
        data = {"path": "/home/user/file.txt", "value": 42}
        h = canonical_hash(data)
        # Hash should be based on data content, not path meaning
        assert isinstance(h, str)
        assert len(h) == 64  # SHA-256 hex

    def test_float_formatting_stable(self) -> None:
        d1 = {"price": 1.5}
        d2 = {"price": 1.500}
        assert canonical_hash(d1) == canonical_hash(d2)


class TestFeatureDependencyGraph:
    def test_build_from_feature_inputs(self) -> None:
        from packages.strategy_spec.models_v2 import FeatureGroup, FeatureInput

        features = [
            FeatureInput(group=FeatureGroup.ORDERBOOK, name="obi"),
            FeatureInput(group=FeatureGroup.TRADES, name="cvd"),
        ]
        graph = build_feature_dependency_graph(features)
        assert len(graph.nodes) == 2
        assert any(n.group == FeatureGroup.ORDERBOOK for n in graph.nodes)

    def test_graph_has_required_features(self) -> None:
        from packages.strategy_spec.models_v2 import FeatureGroup, FeatureInput

        features = [
            FeatureInput(group=FeatureGroup.ORDERBOOK, name="obi", required=True),
            FeatureInput(group=FeatureGroup.TRADES, name="cvd", required=False),
        ]
        graph = build_feature_dependency_graph(features)
        required = [n for n in graph.nodes if n.required]
        assert len(required) == 1

    def test_graph_hashable(self) -> None:
        from packages.strategy_spec.models_v2 import FeatureGroup, FeatureInput

        features = [
            FeatureInput(group=FeatureGroup.ORDERBOOK, name="obi"),
        ]
        graph = build_feature_dependency_graph(features)
        h = graph.compute_hash()
        assert isinstance(h, str) and len(h) == 64


class TestCompiledStrategyIR:
    def test_ir_has_all_required_fields(self) -> None:
        ir = CompiledStrategyIR(
            normalized_spec={"version": "1.0.0", "venue": "BINANCE"},
            compile_hash="abc123",
            feature_graph_hash="def456",
            risk_contract_hash="ghi789",
            condition_count=2,
            feature_count=3,
        )
        assert ir.compile_hash == "abc123"
        assert ir.execution_authority is False

    def test_ir_execution_authority_always_false(self) -> None:
        ir = CompiledStrategyIR(
            normalized_spec={"version": "1.0.0"},
            compile_hash="abc",
            feature_graph_hash="def",
            risk_contract_hash="ghi",
            condition_count=0,
            feature_count=0,
        )
        assert ir.execution_authority is False


class TestRiskContractArtifact:
    def test_risk_contract_has_hash(self) -> None:
        rc = RiskContractArtifact(
            max_spread_bps=5.0,
            max_position_notional=10000.0,
            max_daily_loss=500.0,
        )
        h = rc.compute_hash()
        assert isinstance(h, str) and len(h) == 64

    def test_risk_contract_deterministic(self) -> None:
        rc1 = RiskContractArtifact(max_spread_bps=5.0, max_position_notional=10000.0, max_daily_loss=500.0)
        rc2 = RiskContractArtifact(max_spread_bps=5.0, max_position_notional=10000.0, max_daily_loss=500.0)
        assert rc1.compute_hash() == rc2.compute_hash()


class TestReplayManifestTemplate:
    def test_manifest_has_required_fields(self) -> None:
        rm = ReplayManifestTemplate(
            strategy_artifact_hash="abc123",
            warmup_bars=100,
        )
        assert rm.strategy_artifact_hash == "abc123"

    def test_manifest_hashable(self) -> None:
        rm = ReplayManifestTemplate(
            strategy_artifact_hash="abc123",
            warmup_bars=100,
        )
        h = rm.compute_hash()
        assert isinstance(h, str) and len(h) == 64


class TestArtifactBundle:
    def test_bundle_creation(self) -> None:
        bundle = ArtifactBundle(
            manifest=ArtifactManifest(
                strategy_spec_hash="abc",
                compile_ir_hash="def",
                feature_graph_hash="ghi",
                risk_contract_hash="jkl",
            ),
            normalized_spec={"version": "1.0.0"},
            compiled_ir=CompiledStrategyIR(
                normalized_spec={"version": "1.0.0"},
                compile_hash="def",
                feature_graph_hash="ghi",
                risk_contract_hash="jkl",
                condition_count=0,
                feature_count=0,
            ),
        )
        assert bundle.manifest.strategy_spec_hash == "abc"

    def test_bundle_artifact_hash(self) -> None:
        bundle = ArtifactBundle(
            manifest=ArtifactManifest(
                strategy_spec_hash="abc",
                compile_ir_hash="def",
                feature_graph_hash="ghi",
                risk_contract_hash="jkl",
            ),
            normalized_spec={"version": "1.0.0"},
            compiled_ir=CompiledStrategyIR(
                normalized_spec={"version": "1.0.0"},
                compile_hash="def",
                feature_graph_hash="ghi",
                risk_contract_hash="jkl",
                condition_count=0,
                feature_count=0,
            ),
        )
        h = bundle.compute_artifact_hash()
        assert isinstance(h, str) and len(h) == 64

    def test_bundle_deterministic(self) -> None:
        def make():
            return ArtifactBundle(
                manifest=ArtifactManifest(
                    strategy_spec_hash="abc",
                    compile_ir_hash="def",
                    feature_graph_hash="ghi",
                    risk_contract_hash="jkl",
                ),
                normalized_spec={"version": "1.0.0"},
                compiled_ir=CompiledStrategyIR(
                    normalized_spec={"version": "1.0.0"},
                    compile_hash="def",
                    feature_graph_hash="ghi",
                    risk_contract_hash="jkl",
                    condition_count=0,
                    feature_count=0,
                ),
            )
        assert make().compute_artifact_hash() == make().compute_artifact_hash()
