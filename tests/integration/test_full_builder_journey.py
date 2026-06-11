"""Full Builder journey test — Segment U v4."""
from __future__ import annotations

from packages.strategy_spec.models_v2 import (
    StrategySpecV2,
    StrategySpecV2Metadata,
    StrategySpecV2Universe,
    SchemaVersion,
    FeatureInput,
    FeatureGroup,
    RiskContractV2,
)
from packages.evidence_ledger.models import ArtifactType, EvidenceRef, VerificationStatus
from packages.compatibility.models import CompatibilityMatrix, CompatibilityContract


def _make_v2_spec() -> StrategySpecV2:
    return StrategySpecV2(
        metadata=StrategySpecV2Metadata(
            strategy_id="strat_journey_001",
            lineage_id="lineage_journey",
            name="Journey Test Strategy",
            version="1.0.0",
            schema_version=SchemaVersion.V2,
            created_by="test",
        ),
        universe=StrategySpecV2Universe(
            venue="BINANCE",
            instrument_id="BTCUSDT-PERP.BINANCE",
            timeframe="5-MINUTE",
        ),
        feature_inputs=[FeatureInput(group=FeatureGroup.ORDERBOOK, name="obi")],
        risk_contract=RiskContractV2(
            max_spread_bps=50.0,
            max_position_notional=100000.0,
            max_daily_loss=10000.0,
        ),
    )


class TestFullBuilderJourney:
    def test_step1_v2_creation(self):
        spec = _make_v2_spec()
        assert spec.execution_authority is False
        assert spec.metadata.schema_version == SchemaVersion.V2

    def test_step2_validation_blocks_forbidden(self):
        from packages.strategy_validation.validators import FORBIDDEN_REFERENCES
        assert "submit_order" in FORBIDDEN_REFERENCES

    def test_step3_deterministic_hash(self):
        from packages.strategy_compiler.hashing import canonical_hash
        inputs = {"spec_hash": "abc123", "compiler_version": "0.5.0", "profile": "backtest"}
        assert canonical_hash(inputs) == canonical_hash(inputs)

    def test_step7_evidence_ref(self):
        ref = EvidenceRef(
            evidence_id="ev_journey_001",
            project_id="proj_test",
            artifact_type=ArtifactType.COMPILED_STRATEGY_IR,
            source_system="builder",
            uri="artifact://builder/compile/journey_test",
            sha256="a" * 64,
        )
        assert ref.verification_status == VerificationStatus.UNVERIFIED

    def test_step10_promotion_blocks_no_evidence(self):
        from packages.promotions.gate import PromotionGate, PromotionLevel
        gate = PromotionGate()
        from packages.promotions.gate import PromotionEvidenceSet
        result = gate.evaluate(evidence=PromotionEvidenceSet(), target_level=PromotionLevel.BACKTESTED_SYNTHETIC)
        assert not result.allowed

    def test_step13_compatibility_forbids_live(self):
        contract = CompatibilityContract(
            nautilus_trader_version_pin="1.227.0",
            python_version="3.12",
            strategy_spec_schema_version="2.0",
            feature_schema_version="1.0",
            dataset_manifest_schema_version="1.0",
            compiled_ir_schema_version="1.0",
            promotion_contract_version="1.0",
        )
        matrix = CompatibilityMatrix(
            builder_version="0.5.0",
            contract=contract,
            checked_at="2026-06-11T00:00:00Z",
        )
        assert matrix.is_forbidden("TradeAction")
        assert matrix.is_forbidden("submit_order")

    def test_invariant_no_live_authority(self):
        spec = _make_v2_spec()
        assert spec.execution_authority is False
        from packages.strategy_compiler.hashing import canonical_hash
        h = canonical_hash({"spec": "test", "compiler_version": "0.5.0", "profile": "backtest"})
        assert isinstance(h, str) and len(h) == 64
