"""Object storage factory and service."""
from __future__ import annotations

import os

from packages.object_storage.base import ObjectStorage
from packages.object_storage.local import LocalObjectStorage


def create_object_storage() -> ObjectStorage:
    """Create object storage from environment config."""
    backend = os.environ.get("BUILDER_ARTIFACT_BACKEND", "local")
    root = os.environ.get("BUILDER_ARTIFACT_ROOT", ".artifacts")

    if backend == "local":
        return LocalObjectStorage(root)
    elif backend == "s3":
        # S3 implementation requires boto3; fall back to local if unavailable
        try:
            from packages.object_storage.s3_compatible import S3CompatibleStorage
            return S3CompatibleStorage(
                bucket_url=root,
                region=os.environ.get("AWS_REGION", "us-east-1"),
            )
        except ImportError:
            return LocalObjectStorage(root)
    else:
        return LocalObjectStorage(root)
