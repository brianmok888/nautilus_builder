"""Readiness service — builds the canonical readiness matrix.

v4 spec: capability names match the Reworked Review v4 master prompt.
"""
from __future__ import annotations

from packages.builder_metadata.version import get_canonical_version
from packages.readiness.models import ReadinessEntry, ReadinessMatrix, ReadinessStatus


def get_readiness_matrix() -> ReadinessMatrix:
    """Return the current Builder readiness matrix.

    Capability names follow the v4 spec for cross-reference.
    """
    entries = [
        ReadinessEntry(
            capability="strategy_authoring",
            status=ReadinessStatus.READY,
            required_evidence_types=["strategy_spec_validation"],
            verified_by_command="pytest tests/strategy_spec",
        ),
        ReadinessEntry(
            capability="strategy_validation",
            status=ReadinessStatus.READY,
            required_evidence_types=["validation_report"],
            verified_by_command="pytest tests/strategy_validation",
        ),
        ReadinessEntry(
            capability="strategy_compiler",
            status=ReadinessStatus.PARTIAL,
            required_evidence_types=["deterministic_ir_bundle"],
            blocking_reasons=["full_deterministic_ir_bundle_not_yet_verified"],
            verified_by_command="pytest tests/strategy_compiler",
        ),
        ReadinessEntry(
            capability="synthetic_backtest",
            status=ReadinessStatus.READY,
            required_evidence_types=["backtest_result"],
            verified_by_command="pytest tests/backtest_runner",
        ),
        ReadinessEntry(
            capability="real_dataset_replay",
            status=ReadinessStatus.BLOCKED,
            required_evidence_types=["catalog_dataset_manifest", "replay_manifest"],
            blocking_reasons=[
                "real_parquet_fixtures_not_yet_tested",
                "production_scale_replay_harness_not_landed",
            ],
            verified_by_command="pytest tests/catalog_datasets",
        ),
        ReadinessEntry(
            capability="promotion_contracts",
            status=ReadinessStatus.PARTIAL,
            required_evidence_types=["promotion_evidence_set", "evidence_ledger"],
            blocking_reasons=["promotion_gate_needs_catalog_backtest"],
            verified_by_command="pytest tests/promotions",
        ),
        ReadinessEntry(
            capability="live_execution",
            status=ReadinessStatus.OUT_OF_SCOPE,
            required_evidence_types=["DataTester", "ExecTester", "reconciliation_report"],
            blocking_reasons=["Builder_must_not_own_live_execution"],
        ),
        ReadinessEntry(
            capability="nd_runtime_changes",
            status=ReadinessStatus.OUT_OF_SCOPE,
            required_evidence_types=[],
            blocking_reasons=["Builder_must_not_edit_Nautilus-Daedalus_runtime_code"],
        ),
        ReadinessEntry(
            capability="production_deployment",
            status=ReadinessStatus.PARTIAL,
            required_evidence_types=[
                "ci_gates",
                "auth_enforcement",
                "object_store",
                "service_supervision",
            ],
            blocking_reasons=[
                "ci_security_docker_workflows_pending",
                "startup_fail_closed_needs_production_validation",
            ],
            verified_by_command="bash scripts/verify_all.sh",
        ),
        ReadinessEntry(
            capability="ai_advisory",
            status=ReadinessStatus.READY,
            required_evidence_types=["prompt_audit_store", "validation_gate"],
            verified_by_command="pytest tests/ai_builder",
        ),
    ]
    return ReadinessMatrix(
        builder_version=get_canonical_version(),
        entries=entries,
    )
