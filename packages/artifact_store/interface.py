"""Artifact store abstraction for Nautilus Builder.

Defines the protocol (interface) that all artifact backends must implement.
"""
from __future__ import annotations

from typing import Any, Protocol, runtime_checkable

from .models import ArtifactRecord


@runtime_checkable
class ArtifactStoreProtocol(Protocol):
    """Protocol for artifact storage backends.

    All implementations must provide put() and get() methods.
    Artifacts are always content-addressed and immutable.
    """

    def put(
        self,
        *,
        artifact_type: str,
        artifact_id: str,
        payload: dict[str, Any],
        user_id: str,
        project_id: str,
        content_type: str = "application/json",
    ) -> ArtifactRecord:
        """Store an artifact and return its record.

        Parameters
        ----------
        artifact_type
            Category of artifact (e.g., compile_artifact, replay_result).
        artifact_id
            Unique identifier within the type scope.
        payload
            JSON-serializable artifact content.
        user_id
            Owner user ID.
        project_id
            Owning project ID.
        content_type
            MIME type for the stored artifact.

        Returns
        -------
        ArtifactRecord
            Metadata record including checksum and storage URI.
        """
        ...

    def get(self, artifact_ref: str) -> dict[str, Any]:
        """Retrieve an artifact by its reference.

        Parameters
        ----------
        artifact_ref
            The artifact reference string.

        Returns
        -------
        dict with 'record' (ArtifactRecord) and 'payload' (dict).

        Raises
        ------
        ValueError
            If artifact not found or checksum mismatch.
        """
        ...
