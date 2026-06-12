"""Artifact store abstraction for Nautilus Builder.

Defines the protocol (interface) that all artifact backends must implement.

v6: Unified protocol with put_json/get_json/verify_ref using UserProjectContext.
"""
from __future__ import annotations

from typing import Any, Protocol, runtime_checkable

from packages.auth import UserProjectContext

from .models import ArtifactRecord, StoredJsonArtifact


@runtime_checkable
class ArtifactStoreProtocol(Protocol):
    """Protocol for artifact storage backends.

    All implementations must provide put_json, get_json, and verify_ref.
    Artifacts are always content-addressed and immutable.
    """

    def put_json(
        self,
        *,
        context: UserProjectContext,
        artifact_type: str,
        artifact_id: str,
        payload: dict[str, Any],
        metadata: dict[str, str] | None = None,
    ) -> ArtifactRecord:
        """Store a JSON artifact and return its record."""
        ...

    def get_json(
        self,
        *,
        context: UserProjectContext,
        artifact_ref: str,
    ) -> StoredJsonArtifact:
        """Retrieve a JSON artifact by reference, scoped to context.

        Raises ValueError if artifact not found, scope mismatch, or checksum mismatch.
        """
        ...

    def verify_ref(
        self,
        *,
        context: UserProjectContext,
        artifact_ref: str,
        expected_sha256: str | None = None,
    ) -> ArtifactRecord:
        """Verify an artifact exists and has valid checksum.

        Returns the ArtifactRecord if verification passes.
        Raises ValueError if artifact not found, scope mismatch, or checksum mismatch.
        """
        ...
