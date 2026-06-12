"""In-memory evidence repository for local/dev/demo use only.

Must NOT be used in production. Production requires PostgresEvidenceRepository.
"""
from __future__ import annotations

from packages.evidence_ledger.models import EvidenceRef
from packages.evidence_ledger.verifier import verify_evidence_ref


class InMemoryEvidenceRepository:
    """In-memory evidence storage for local/dev/demo only.

    NOT suitable for production: data is lost on restart.
    """

    def __init__(self) -> None:
        self._store: dict[str, EvidenceRef] = {}

    def save(self, ref: EvidenceRef) -> EvidenceRef:
        """Save and verify an evidence ref."""
        verified = verify_evidence_ref(ref)
        self._store[verified.evidence_id] = verified
        return verified

    def get(self, evidence_id: str, project_id: str) -> EvidenceRef | None:
        """Get an evidence ref by ID, scoped to project."""
        ref = self._store.get(evidence_id)
        if ref is None or ref.project_id != project_id:
            return None
        return ref

    def list_by_project(self, project_id: str) -> list[EvidenceRef]:
        """List all evidence refs for a project."""
        return [ref for ref in self._store.values() if ref.project_id == project_id]

    def list_by_strategy_lineage(
        self, project_id: str, strategy_lineage_id: str
    ) -> list[EvidenceRef]:
        """List evidence refs for a strategy lineage within a project."""
        return [
            ref
            for ref in self._store.values()
            if ref.project_id == project_id
            and ref.strategy_lineage_id == strategy_lineage_id
        ]
