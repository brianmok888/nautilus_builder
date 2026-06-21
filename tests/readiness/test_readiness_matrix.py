"""Tests for readiness model and service — v4 capability names."""
from __future__ import annotations

import pytest

from packages.readiness.models import ReadinessEntry, ReadinessMatrix, ReadinessStatus
from packages.readiness.service import get_readiness_matrix


class TestReadinessModels:
    def test_readiness_entry_requires_capability(self):
        entry = ReadinessEntry(
            capability="test",
            status=ReadinessStatus.READY,
        )
        assert entry.capability == "test"
        assert entry.status == ReadinessStatus.READY

    def test_readiness_matrix_has_entries(self):
        matrix = get_readiness_matrix()
        assert len(matrix.entries) >= 10  # v4 spec requires 10 capabilities

    def test_live_execution_is_out_of_scope(self):
        matrix = get_readiness_matrix()
        assert not matrix.live_execution_ready
        live_entry = [e for e in matrix.entries if e.capability == "live_execution"][0]
        assert live_entry.status == ReadinessStatus.OUT_OF_SCOPE

    def test_guard_live_execution_never_ready(self):
        """Guard: if any future change flips live_execution to ready, this test catches it."""
        matrix = get_readiness_matrix()
        for entry in matrix.entries:
            if entry.capability == "live_execution":
                assert entry.status == ReadinessStatus.OUT_OF_SCOPE, (
                    "Builder must never claim live execution readiness"
                )

    def test_all_entries_have_status(self):
        matrix = get_readiness_matrix()
        for entry in matrix.entries:
            assert isinstance(entry.status, ReadinessStatus)

    def test_matrix_has_builder_version(self):
        matrix = get_readiness_matrix()
        assert matrix.builder_version != ""
        assert matrix.builder_version != "0.0.0-unknown"

    def test_readiness_entry_extra_fields_forbidden(self):
        with pytest.raises(Exception):
            ReadinessEntry(
                capability="test",
                status=ReadinessStatus.READY,
                unknown="bad",
            )


class TestReadinessService:
    def test_expected_v4_capabilities_present(self):
        matrix = get_readiness_matrix()
        caps = {e.capability for e in matrix.entries}
        expected = {
            "strategy_authoring",
            "strategy_validation",
            "strategy_compiler",
            "synthetic_backtest",
            "real_dataset_replay",
            "promotion_contracts",
            "live_execution",
            "nd_runtime_changes",
            "production_deployment",
            "ai_advisory",
        }
        assert expected.issubset(caps), f"Missing capabilities: {expected - caps}"

    def test_blocked_entries_have_reasons(self):
        matrix = get_readiness_matrix()
        for entry in matrix.entries:
            if entry.status == ReadinessStatus.BLOCKED:
                assert len(entry.blocking_reasons) > 0, (
                    f"Blocked entry {entry.capability} has no blocking reasons"
                )

    def test_nd_runtime_changes_is_out_of_scope(self):
        matrix = get_readiness_matrix()
        nd = [e for e in matrix.entries if e.capability == "nd_runtime_changes"]
        assert len(nd) == 1
        assert nd[0].status == ReadinessStatus.OUT_OF_SCOPE


class ReadinessOverstatementGuardTest:
    """Lock the evidence-gated invariant: no capability may overstate
    production/live readiness without its required evidence types, and the
    production-deployment capability must never be READY in Builder."""

    def test_production_deployment_is_never_ready(self) -> None:
        matrix = get_readiness_matrix()
        prod = [e for e in matrix.entries if e.capability == "production_deployment"]
        assert prod, "production_deployment capability must exist in the matrix"
        assert prod[0].status != ReadinessStatus.READY, (
            "Builder must never label production_deployment as READY; it is "
            "scaffold/contract/evidence-gated only until CI gates, auth "
            "enforcement, object storage, and service supervision land."
        )

    def test_every_ready_entry_declares_required_evidence_types(self) -> None:
        """A READY capability must still declare its required evidence types so
        the payload cannot imply production/live readiness without an evidence
        gate. This guards against future entries that flip to READY while
        dropping the evidence contract."""
        matrix = get_readiness_matrix()
        for entry in matrix.entries:
            if entry.status == ReadinessStatus.READY:
                assert entry.required_evidence_types, (
                    f"READY capability '{entry.capability}' declares no "
                    "required_evidence_types; it may overstate production "
                    "readiness without an evidence gate."
                )

    def test_no_capability_claims_live_or_production_in_name_as_ready(self) -> None:
        """Defensive: any capability whose name implies live/production execution
        must not be READY. Catches future naming that could overstate readiness."""
        matrix = get_readiness_matrix()
        sentinel_names = ("live_execution", "production_deployment", "live", "production")
        for entry in matrix.entries:
            name = entry.capability.lower()
            if any(s in name for s in sentinel_names):
                assert entry.status != ReadinessStatus.READY, (
                    f"Capability '{entry.capability}' implies live/production "
                    "readiness but is marked READY; Builder is evidence-gated "
                    "scaffold/contract only and must not claim production/live."
                )
