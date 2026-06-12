"""Shared API route dependencies."""
from __future__ import annotations

from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class RateLimiterProtocol(Protocol):
    def is_allowed(self, key: str) -> bool: ...


@runtime_checkable
class ArtifactStoreProtocol(Protocol):
    def write_artifact(self, key: str, data: bytes) -> str: ...
    def read_artifact(self, key: str) -> bytes | None: ...


@runtime_checkable
class EvidenceRepositoryProtocol(Protocol):
    """Protocol for evidence storage backends."""

    def save(self, ref: Any) -> Any:
        """Save an evidence ref."""
        ...

    def get(self, evidence_id: str, project_id: str) -> Any | None:
        """Get an evidence ref by ID, scoped to project."""
        ...

    def list_by_project(self, project_id: str) -> list[Any]:
        """List all evidence refs for a project."""
        ...

    def list_by_strategy_lineage(self, project_id: str, strategy_lineage_id: str) -> list[Any]:
        """List evidence refs for a strategy lineage within a project."""
        ...
