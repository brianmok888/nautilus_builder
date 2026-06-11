"""Parquet manifest validation utilities."""
from __future__ import annotations

from packages.catalog_datasets.models import DatasetManifest


def validate_manifest(manifest: DatasetManifest) -> list[str]:
    """Validate a dataset manifest for completeness and consistency.

    Returns a list of warning/error strings. Empty list means valid.
    """
    errors: list[str] = []

    # SHA-256 should be 64 hex characters for real manifests
    if len(manifest.content_sha256) != 64:
        errors.append(
            f"content_sha256 is {len(manifest.content_sha256)} chars, expected 64 hex digits"
        )

    # Row count should be positive
    if manifest.row_count == 0:
        errors.append("row_count is 0 — dataset appears empty")

    # Date range sanity
    if manifest.start_ts >= manifest.end_ts:
        errors.append("start_ts must be before end_ts")

    # Storage URI should be a valid scheme
    if not any(manifest.storage_uri.startswith(s) for s in ("s3://", "gs://", "file://", "local", "/")):
        errors.append(f"storage_uri scheme unclear: {manifest.storage_uri[:50]}")

    return errors
