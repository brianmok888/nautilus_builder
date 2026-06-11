"""Readiness service — builds the canonical readiness matrix."""
from __future__ import annotations

from packages.builder_metadata.version import get_canonical_version
from packages.readiness.models import ReadinessEntry, ReadinessMatrix, ReadinessStatus


def get_readiness_matrix() -> ReadinessMatrix:
    """Return the current Builder readiness matrix."""
    entries = [
        ReadinessEntry(
            capability="builder_authoring_ready",
            status=ReadinessStatus.READY,
            required_evidence_types=["strategy_spec_validation"],
            verified_by_command="pytest tests/strategy_spec",
        ),
        ReadinessEntry(
            capability="strategy_validation_ready",
            status=ReadinessStatus.READY,
            required_evidence_types=["validation_report"],
            verified_by_command="pytest tests/strategy_validation",
        ),
        ReadinessEntry(
            capability="synthetic_backtest_ready",
            status=ReadinessStatus.READY,
            required_evidence_types=["backtest_result"],
            verified_by_command="pytest tests/backtest_runner",
        ),
        ReadinessEntry(
            capability="catalog_replay_smoke_ready",
            status=ReadinessStatus.READY,
            required_evidence_types=["replay_manifest"],
            verified_by_command="pytest tests/backtest_runner -k catalog",
        ),
        ReadinessEntry(
            capability="real_dataset_replay_ready",
            status=ReadinessStatus.PARTIAL,
            required_evidence_types=["catalog_dataset_manifest", "replay_manifest"],
            blocking_reasons=["real_parquet_fixtures_not_yet_tested"],
            verified_by_command="pytest tests/catalog_datasets",
        ),
        ReadinessEntry(
            capability="promotion_contract_ready",
            status=ReadinessStatus.PARTIAL,
            required_evidence_types=["promotion_evidence_set"],
            blocking_reasons=["promotion_gate_needs_catalog_backtest"],
        ),
        ReadinessEntry(
            capability="shadow_signal_preview_ready",
            status=ReadinessStatus.BLOCKED,
            required_evidence_types=["execution_lane_contract"],
            blocking_reasons=["requires_external_runtime"],
        ),
        ReadinessEntry(
            capability="paper_execution_observability_ready",
            status=ReadinessStatus.BLOCKED,
            required_evidence_types=["runtime_events", "audit_lineage"],
            blocking_reasons=["requires_external_runtime"],
        ),
        ReadinessEntry(
            capability="live_execution",
            status=ReadinessStatus.OUT_OF_SCOPE,
            required_evidence_types=["DataTester", "ExecTester", "reconciliation_report"],
            blocking_reasons=["Builder_must_not_own_live_execution"],
        ),
    ]
    return ReadinessMatrix(
        builder_version=get_canonical_version(),
        entries=entries,
    )
