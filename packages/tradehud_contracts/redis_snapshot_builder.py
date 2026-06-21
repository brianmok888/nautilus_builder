"""TradeHUD Redis snapshot builder — assemble a TradeHudSnapshot from entries.

Extracted from redis_adapter.py. `build_snapshot_from_redis` is the public entry
point used by the adapter to convert collected Redis stream entries into a single
`TradeHudSnapshot`.
"""

from __future__ import annotations

from typing import Any

from packages.tradehud_contracts.models import TradeHudSnapshot
from packages.tradehud_contracts.redis_normalizers import parse_stream_entry


def build_snapshot_from_redis(entries: dict[str, dict[bytes, bytes]]) -> TradeHudSnapshot:
    """Build a TradeHudSnapshot from collected Redis stream entries."""
    snapshot_fields: dict[str, Any] = {}
    for suffix, fields in entries.items():
        parsed = parse_stream_entry(suffix, fields)
        if parsed:
            field_name, model = parsed
            snapshot_fields[field_name] = model
    snapshot = TradeHudSnapshot(**snapshot_fields)
    snapshot.provenance = "redis"
    return snapshot
