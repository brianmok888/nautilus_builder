"""Local filesystem object storage backend."""
from __future__ import annotations

from pathlib import Path

from packages.object_storage.base import ObjectStorage


class LocalObjectStorage(ObjectStorage):
    """Store objects as files in a local directory."""

    def __init__(self, root: str | Path) -> None:
        self._root = Path(root)
        self._root.mkdir(parents=True, exist_ok=True)

    def _resolve(self, key: str) -> Path:
        # Prevent path traversal
        resolved = (self._root / key).resolve()
        if not str(resolved).startswith(str(self._root.resolve())):
            raise ValueError(f"Path traversal detected: {key}")
        return resolved

    def write(self, key: str, data: bytes) -> str:
        path = self._resolve(key)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        return f"local://{path}"

    def read(self, key: str) -> bytes | None:
        path = self._resolve(key)
        if not path.exists():
            return None
        return path.read_bytes()

    def exists(self, key: str) -> bool:
        return self._resolve(key).exists()

    def delete(self, key: str) -> bool:
        path = self._resolve(key)
        if path.exists():
            path.unlink()
            return True
        return False
