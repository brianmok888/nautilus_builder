"""Object storage abstraction — local and S3-compatible backends."""
from packages.object_storage.base import ObjectStorage
from packages.object_storage.local import LocalObjectStorage

__all__ = ["ObjectStorage", "LocalObjectStorage"]
