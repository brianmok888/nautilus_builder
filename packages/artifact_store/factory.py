"""Artifact store factory for Nautilus Builder.

Creates the appropriate backend based on BUILDER_ARTIFACT_BACKEND env var:
- ``local`` (default): LocalJsonArtifactStore
- ``s3``: S3ArtifactStore (requires boto3)

Environment variables for S3:
- BUILDER_ARTIFACT_BACKEND: ``local`` or ``s3`` (default: ``local``)
- BUILDER_S3_ENDPOINT_URL: Optional MinIO/compatible endpoint
- BUILDER_S3_BUCKET: Required for s3 backend
- BUILDER_S3_REGION: AWS region (default: ``us-east-1``)
- BUILDER_S3_ACCESS_KEY_ID: AWS access key
- BUILDER_S3_SECRET_ACCESS_KEY: AWS secret key

S3 secrets are NEVER exposed to the frontend.
"""
from __future__ import annotations

import os
from typing import Any



def create_artifact_store(
    *,
    local_root: str | None = None,
) -> Any:
    """Create the appropriate artifact store based on environment config.

    Parameters
    ----------
    local_root
        Root directory for the local JSON artifact store.

    Returns
    -------
    ArtifactStoreProtocol
        Either LocalJsonArtifactStore or S3ArtifactStore.
    """
    backend = os.environ.get("BUILDER_ARTIFACT_BACKEND", "local").strip().lower()
    configured_local_root = local_root or os.environ.get("BUILDER_ARTIFACT_ROOT", ".artifacts").strip() or ".artifacts"

    if backend == "s3":
        return _create_s3_store()
    if backend == "local":
        return _create_local_store(root=configured_local_root)
    raise ValueError(
        f"Unknown BUILDER_ARTIFACT_BACKEND: '{backend}'. Must be 'local' or 's3'."
    )


def _create_s3_store() -> Any:
    """Create an S3ArtifactStore from environment configuration."""
    bucket = os.environ.get("BUILDER_S3_BUCKET", "").strip()
    if not bucket:
        raise ValueError("BUILDER_S3_BUCKET is required when BUILDER_ARTIFACT_BACKEND=s3")

    region = os.environ.get("BUILDER_S3_REGION", "us-east-1").strip()
    endpoint_url = os.environ.get("BUILDER_S3_ENDPOINT_URL", "").strip() or None
    access_key = os.environ.get("BUILDER_S3_ACCESS_KEY_ID", "").strip()
    secret_key = os.environ.get("BUILDER_S3_SECRET_ACCESS_KEY", "").strip()

    try:
        import boto3
    except ImportError as exc:
        raise ImportError(
            "boto3 is required for S3 artifact storage. "
            "Install with: pip install boto3"
        ) from exc

    client_kwargs: dict[str, Any] = {
        "region_name": region,
    }
    if endpoint_url:
        client_kwargs["endpoint_url"] = endpoint_url
    if access_key and secret_key:
        client_kwargs["aws_access_key_id"] = access_key
        client_kwargs["aws_secret_access_key"] = secret_key

    s3_client = boto3.client("s3", **client_kwargs)

    from .s3_store import S3ArtifactStore
    return S3ArtifactStore(
        s3_client=s3_client,
        bucket=bucket,
        endpoint_url=endpoint_url,
    )


def _create_local_store(*, root: str) -> Any:
    """Create a LocalJsonArtifactStore."""
    from .service import LocalJsonArtifactStore
    return LocalJsonArtifactStore(root=root)
