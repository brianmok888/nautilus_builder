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
