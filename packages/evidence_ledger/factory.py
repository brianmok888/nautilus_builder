"""Factory + environment guard for evidence repositories.

``create_fastapi_app`` enforces persistent evidence storage at startup, but a
worker, CLI, or other entrypoint that constructs evidence services directly could
bypass that guard. This factory provides defense-in-depth: it rejects an
in-memory repository outside LOCAL mode regardless of the construction path.
"""
from __future__ import annotations

from packages.auth.policy import BuilderEnvironment
from packages.evidence_ledger.in_memory_repository import InMemoryEvidenceRepository
from packages.evidence_ledger.models import EvidenceRef  # noqa: F401  (re-export convenience)


def create_evidence_repository_for_env(repo, *, environment: BuilderEnvironment):
    """Return ``repo`` unchanged, or raise if an in-memory repo is used outside
    LOCAL mode.

    Persistent repositories (Postgres-backed) are always allowed. In-memory is
    allowed only in LOCAL; in PRODUCTION/STAGING an in-memory repo would lose
    evidence on restart, so we fail closed.
    """
    if environment == BuilderEnvironment.LOCAL:
        return repo
    if isinstance(repo, InMemoryEvidenceRepository):
        raise ValueError(
            "Persistent evidence storage is required outside local mode "
            "(in-memory repository rejected by create_evidence_repository_for_env). "
            "Set BUILDER_DATABASE_URL or use local mode."
        )
    return repo
