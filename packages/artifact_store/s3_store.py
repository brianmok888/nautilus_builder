"""S3-compatible artifact store for Nautilus Builder.

Uses content-addressed immutable keys:
    artifacts/{project_id}/{user_id}/{artifact_type}/{sha256}/{artifact_id}.json

Supports MinIO for local/staging by configuring BUILDER_S3_ENDPOINT_URL.

boto3 is an optional dependency — import failure raises a clear error.

v6: Added put_json/get_json/verify_ref with UserProjectContext parity.
"""
from __future__ import annotations

import hashlib
import json
import re
from datetime import UTC, datetime
from typing import Any

from packages.auth import UserProjectContext

from .models import ArtifactRecord, StoredJsonArtifact

_SAFE_IDENTIFIER = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.:-]*$")
_S3_PREFIX = "s3://"


class S3ArtifactStore:
    """S3-compatible artifact store with content-addressed immutable keys.

    Parameters
    ----------
    s3_client
        A boto3 S3 client (or compatible mock).
    bucket
        S3 bucket name.
    endpoint_url
        Optional endpoint URL for MinIO or other S3-compatible stores.
    """

    def __init__(
        self,
        *,
        s3_client: Any,
        bucket: str,
        endpoint_url: str | None = None,
    ) -> None:
        self._client = s3_client
        self._bucket = bucket
        self._endpoint_url = endpoint_url

    # --- Unified protocol: put_json / get_json / verify_ref ---

    def put_json(
        self,
        *,
        context: UserProjectContext,
        artifact_type: str,
        artifact_id: str,
        payload: dict[str, Any],
        metadata: dict[str, str] | None = None,
    ) -> ArtifactRecord:
        """Store a JSON artifact with user/project context."""
        return self.put(
            artifact_type=artifact_type,
            artifact_id=artifact_id,
            payload=payload,
            user_id=context.user_id,
            project_id=context.project_id,
            metadata=metadata,
        )

    def get_json(
        self,
        *,
        context: UserProjectContext,
        artifact_ref: str,
    ) -> StoredJsonArtifact:
        """Retrieve and verify a JSON artifact, scoped to context."""
        result = self.get(artifact_ref)
        record = result["record"]
        # Verify project scope
        if record.project_id != context.project_id:
            raise ValueError(
                f"artifact scope mismatch: artifact project={record.project_id}, "
                f"context project={context.project_id}"
            )
        return StoredJsonArtifact(record=record, payload=result["payload"])

    def verify_ref(
        self,
        *,
        context: UserProjectContext,
        artifact_ref: str,
        expected_sha256: str | None = None,
    ) -> ArtifactRecord:
        """Verify an artifact exists and has valid checksum."""
        result = self.get(artifact_ref)
        record = result["record"]
        if record.project_id != context.project_id:
            raise ValueError(
                f"artifact scope mismatch: artifact project={record.project_id}, "
                f"context project={context.project_id}"
            )
        if expected_sha256 and record.checksum_sha256 != expected_sha256:
            raise ValueError(
                f"artifact checksum mismatch: expected={expected_sha256}, "
                f"actual={record.checksum_sha256}"
            )
        return record

    # --- Legacy protocol: put / get ---

    def put(
        self,
        *,
        artifact_type: str,
        artifact_id: str,
        payload: dict[str, Any],
        user_id: str,
        project_id: str,
        content_type: str = "application/json",
        metadata: dict[str, str] | None = None,
    ) -> ArtifactRecord:
        safe_type = _validate_identifier(artifact_type)
        safe_id = _validate_identifier(artifact_id)
        safe_user = _validate_identifier(user_id)
        safe_project = _validate_identifier(project_id)

        body_bytes = _canonical_json_bytes(payload)
        checksum = hashlib.sha256(body_bytes).hexdigest()

        # Content-addressed key: artifacts/{project}/{user}/{type}/{sha256}/{id}.json
        key = f"artifacts/{safe_project}/{safe_user}/{safe_type}/{checksum}/{safe_id}.json"
        uri = f"{_S3_PREFIX}{self._bucket}/{key}"

        s3_metadata = {
            "artifact-type": safe_type,
            "artifact-id": safe_id,
            "user-id": safe_user,
            "project-id": safe_project,
            "checksum-sha256": checksum,
            "execution-authority": "false",
        }
        if metadata:
            for k, v in metadata.items():
                s3_metadata[f"custom-{k}"] = v

        self._client.put_object(
            Bucket=self._bucket,
            Key=key,
            Body=body_bytes,
            ContentType=content_type,
            Metadata=s3_metadata,
        )

        return ArtifactRecord(
            artifact_ref=uri,
            artifact_type=safe_type,
            artifact_id=safe_id,
            user_id=safe_user,
            project_id=safe_project,
            path=key,
            checksum_sha256=checksum,
            content_type=content_type,
            created_at=datetime.now(UTC).isoformat().replace("+00:00", "Z"),
            metadata={
                "execution_authority": "false",
                "storage_backend": "s3",
            },
        )

    def get(self, artifact_ref: str) -> dict[str, Any]:
        """Retrieve an artifact by its S3 URI or artifact ref.

        Verifies checksum after reading. Raises on mismatch.
        """
        key = self._resolve_key(artifact_ref)
        response = self._client.get_object(Bucket=self._bucket, Key=key)
        body_bytes = response["Body"].read()

        try:
            payload = json.loads(body_bytes)
        except (json.JSONDecodeError, TypeError) as exc:
            raise ValueError(f"artifact payload invalid JSON: {artifact_ref}") from exc

        if not isinstance(payload, dict):
            raise ValueError(f"artifact payload must be a JSON object: {artifact_ref}")

        # Verify checksum
        actual_checksum = hashlib.sha256(body_bytes).hexdigest()

        # Try to get expected checksum from metadata
        metadata = response.get("Metadata", {})
        expected_checksum = metadata.get("checksum-sha256")

        # If no metadata checksum, compute from the payload itself
        if expected_checksum and actual_checksum != expected_checksum:
            raise ValueError(
                f"artifact checksum mismatch for {artifact_ref}: "
                f"expected {expected_checksum}, got {actual_checksum}"
            )

        record = ArtifactRecord(
            artifact_ref=artifact_ref,
            artifact_type=metadata.get("artifact-type", "unknown"),
            artifact_id=metadata.get("artifact-id", "unknown"),
            user_id=metadata.get("user-id", "unknown"),
            project_id=metadata.get("project-id", "unknown"),
            path=key,
            checksum_sha256=actual_checksum,
            content_type=response.get("ContentType", "application/json"),
            created_at=datetime.now(UTC).isoformat().replace("+00:00", "Z"),
            metadata=dict(metadata),
        )

        return {"record": record, "payload": payload}

    def _resolve_key(self, artifact_ref: str) -> str:
        """Extract the S3 key from an artifact reference."""
        if artifact_ref.startswith(_S3_PREFIX):
            # s3://bucket/key -> key
            without_prefix = artifact_ref[len(_S3_PREFIX):]
            slash_idx = without_prefix.find("/")
            if slash_idx < 0:
                raise ValueError(f"invalid S3 artifact ref: {artifact_ref}")
            return without_prefix[slash_idx + 1:]
        raise ValueError(f"unsupported artifact ref format: {artifact_ref}")


def _canonical_json_bytes(payload: dict[str, Any]) -> bytes:
    return json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _validate_identifier(value: str) -> str:
    if _SAFE_IDENTIFIER.fullmatch(value) is None:
        raise ValueError(f"safe identifier required: {value}")
    return value
