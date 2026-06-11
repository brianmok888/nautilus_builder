"""Abstract base for object storage backends."""
from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path


class ObjectStorage(ABC):
    """Abstract interface for reading/writing binary objects."""

    @abstractmethod
    def write(self, key: str, data: bytes) -> str:
        """Write an object. Returns the storage URI."""
        ...

    @abstractmethod
    def read(self, key: str) -> bytes | None:
        """Read an object. Returns None if not found."""
        ...

    @abstractmethod
    def exists(self, key: str) -> bool:
        """Check if an object exists."""
        ...

    @abstractmethod
    def delete(self, key: str) -> bool:
        """Delete an object. Returns True if deleted."""
        ...
