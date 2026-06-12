"""Evidence route handlers — CRUD for typed evidence refs.

Uses injected repository for storage.
Production must use PostgresEvidenceRepository; local/dev uses InMemoryEvidenceRepository.

v6: verify_evidence uses enhanced verifier with source system, expiry,
    hex format, and optional artifact store integration.
"""
from __future__ import annotations

from typing import Any

from packages.evidence_ledger.models import EvidenceRef
from packages.evidence_ledger.verifier import verify_evidence_ref


def create_evidence(
    payload: dict[str, Any],
    *,
    repo: Any,
) -> dict[str, Any]:
    """Create and store a new evidence reference."""
    ref = EvidenceRef(**payload)
    saved = repo.save(ref)
    return saved.model_dump()


def get_evidence(
    evidence_id: str,
    *,
    project_id: str,
    repo: Any,
) -> dict[str, Any] | None:
    """Retrieve an evidence reference by ID, scoped to project."""
    ref = repo.get(evidence_id, project_id)
    return ref.model_dump() if ref else None


def verify_evidence(
    evidence_id: str,
    *,
    project_id: str,
    repo: Any,
    artifact_store: Any | None = None,
) -> dict[str, Any] | None:
    """Re-verify an evidence reference using the enhanced verifier."""
    ref = repo.get(evidence_id, project_id)
    if not ref:
        return None
    verified = verify_evidence_ref(
        ref,
        artifact_store=artifact_store,
        context_project_id=project_id,
    )
    # Use update_verification to persist the result
    updated = repo.update_verification(
        evidence_id=evidence_id,
        project_id=project_id,
        verification_status=verified.verification_status,
        error=verified.verification_error,
    )
    if updated is not None:
        return updated.model_dump()
    return verified.model_dump()


def list_evidence_for_strategy(
    strategy_lineage_id: str,
    *,
    project_id: str,
    repo: Any,
) -> list[dict[str, Any]]:
    """List all evidence refs for a strategy lineage."""
    if not strategy_lineage_id:
        return [r.model_dump() for r in repo.list_by_project(project_id)]
    return [
        r.model_dump()
        for r in repo.list_by_strategy_lineage(project_id, strategy_lineage_id)
    ]
