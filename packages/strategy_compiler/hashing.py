"""Deterministic hashing utilities for compiler artifacts.

Rules:
- Canonical JSON serialization
- Sorted object keys
- No wall-clock timestamps inside hash material
- No local absolute paths inside hash material
- Same input produces same hash on any machine
"""
from __future__ import annotations

import hashlib
import json
from typing import Any


def deterministic_json(data: Any) -> str:
    """Serialize data to a deterministic JSON string.

    - Sorted keys
    - No whitespace separators
    - Floats are kept as-is (Python json handles 1.5 == 1.500)
    - No local paths stripped — caller must sanitize data before hashing
    """
    return json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def canonical_hash(data: Any) -> str:
    """Compute SHA-256 hash of data using deterministic JSON serialization."""
    encoded = deterministic_json(data).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()
