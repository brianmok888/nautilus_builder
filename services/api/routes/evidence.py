"""Evidence route handlers — CRUD for typed evidence refs."""
from __future__ import annotations

from typing import Any

from packages.evidence_ledger.models import EvidenceRef
from packages.evidence_ledger.verifier import verify_evidence_ref


# In-memory evidence store for dev/demo. Production uses persistence layer.
_evidence_store: dict[str, EvidenceRef] = {}


def create_evidence(payload: dict[str, Any]) -> dict[str, Any]:
    """Create and store a new evidence reference."""
    ref = EvidenceRef(**payload)
    verified = verify_evidence_ref(ref)
    _evidence_store[verified.evidence_id] = verified
    return verified.model_dump()


def get_evidence(evidence_id: str) -> dict[str, Any] | None:
    """Retrieve an evidence reference by ID."""
    ref = _evidence_store.get(evidence_id)
    return ref.model_dump() if ref else None


def verify_evidence(evidence_id: str) -> dict[str, Any] | None:
    """Re-verify an evidence reference."""
    ref = _evidence_store.get(evidence_id)
    if not ref:
        return None
    verified = verify_evidence_ref(ref)
    _evidence_store[evidence_id] = verified
    return verified.model_dump()


def list_evidence_for_strategy(strategy_lineage_id: str) -> list[dict[str, Any]]:
    """List all evidence refs for a strategy lineage."""
    if not strategy_lineage_id:
        return [ref.model_dump() for ref in _evidence_store.values()]
    return [
        ref.model_dump()
        for ref in _evidence_store.values()
        if ref.strategy_lineage_id == strategy_lineage_id
    ]
