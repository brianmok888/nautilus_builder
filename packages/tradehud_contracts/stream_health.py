"""Per-stream health tracking for Redis-backed TradeHUD data.

Tracks last-seen timestamps, staleness, and availability per stream.
Emits stream_health SSE events.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any

from packages.tradehud_contracts.config import TradeHudRedisConfig


@dataclass
class StreamHealthEntry:
    """Health state for a single Redis stream."""
    stream_key: str = ""
    logical_name: str = ""
    last_entry_id: str | None = None
    last_event_ts_ns: int | None = None
    last_receive_ts_ns: int | None = None
    age_ms: int | None = None
    events_seen: int = 0
    last_error: str | None = None
    status: str = "unknown"  # live | stale | missing | unavailable | unknown | synthetic


class StreamHealthTracker:
    """Tracks health for all configured Redis streams."""

    def __init__(self, config: TradeHudRedisConfig) -> None:
        self._config = config
        self._streams: dict[str, StreamHealthEntry] = {}
        self._connected = False
        now_ns = int(time.time() * 1_000_000_000)
        stream_map = config.get_stream_map()
        for logical_name, stream_key in stream_map.items():
            self._streams[logical_name] = StreamHealthEntry(
                stream_key=stream_key,
                logical_name=logical_name,
                last_receive_ts_ns=now_ns,
            )

    def mark_connected(self, connected: bool) -> None:
        """Update Redis connection state."""
        self._connected = connected
        if not connected:
            for entry in self._streams.values():
                if entry.status not in ("unknown",):
                    entry.status = "unavailable"
                    entry.last_error = "redis_unavailable"
        else:
            for entry in self._streams.values():
                if entry.status == "unavailable":
                    entry.last_error = None

    def record_event(self, logical_name: str, entry_id: str, event_ts_ns: int | None) -> None:
        """Record that we received an event from a stream."""
        if logical_name not in self._streams:
            return
        entry = self._streams[logical_name]
        entry.last_entry_id = entry_id
        entry.last_event_ts_ns = event_ts_ns
        entry.last_receive_ts_ns = int(time.time() * 1_000_000_000)
        entry.events_seen += 1
        entry.last_error = None
        if self._connected:
            entry.status = "live"

    def record_seed(self, logical_name: str, entry_id: str | None, event_ts_ns: int | None) -> None:
        """Record a seeded/initial entry from XREVRANGE.

        Real Redis data seeded via XREVRANGE is NOT synthetic.
        Status is determined by freshness of the event timestamp.
        """
        if logical_name not in self._streams:
            return
        entry = self._streams[logical_name]
        if entry_id:
            entry.last_entry_id = entry_id
        if event_ts_ns:
            entry.last_event_ts_ns = event_ts_ns
        entry.last_receive_ts_ns = int(time.time() * 1_000_000_000)
        entry.events_seen += 1
        if not entry_id:
            entry.status = "missing"
        elif event_ts_ns:
            now_ms = int(time.time() * 1_000)
            age = now_ms - (event_ts_ns // 1_000_000)
            entry.age_ms = age
            if age > self._config.stream_stale_ms:
                entry.status = "stale"
            else:
                entry.status = "live"  # Real Redis data, fresh
        else:
            entry.status = "unknown"  # Has entry but no timestamp

    def record_error(self, logical_name: str, error: str) -> None:
        if logical_name not in self._streams:
            return
        self._streams[logical_name].last_error = error

    def evaluate(self) -> dict[str, Any]:
        """Evaluate all stream health based on staleness thresholds.

        Returns health summary for SSE stream_health events.
        """
        now_ns = int(time.time() * 1_000_000_000)
        now_ms = now_ns // 1_000_000

        seen = []
        missing = []
        stale = []
        unavailable = []

        for entry in self._streams.values():
            if entry.status == "unavailable":
                unavailable.append(entry.stream_key)
                continue
            if not entry.last_entry_id and not entry.last_event_ts_ns:
                if (now_ms - (entry.last_receive_ts_ns // 1_000_000 if entry.last_receive_ts_ns else now_ms)) > self._config.stream_missing_ms:
                    entry.status = "missing"
                    missing.append(entry.stream_key)
                continue

            if entry.last_event_ts_ns:
                event_ms = entry.last_event_ts_ns // 1_000_000
                age = now_ms - event_ms
                entry.age_ms = age
                if age > self._config.stream_stale_ms:
                    entry.status = "stale"
                    stale.append(entry.stream_key)
                else:
                    if self._connected:
                        entry.status = "live"
                seen.append(entry.stream_key)
            elif entry.last_entry_id:
                seen.append(entry.stream_key)

        return {
            "feed_source": self._config.feed_source,
            "redis_connected": self._connected,
            "streams_seen": seen,
            "streams_missing": missing,
            "streams_stale": stale,
            "streams_unavailable": unavailable,
            "last_event_ts": max(
                (e.last_event_ts_ns for e in self._streams.values() if e.last_event_ts_ns),
                default=None,
            ),
            "last_error": next(
                (e.last_error for e in self._streams.values() if e.last_error),
                None,
            ),
            "stream_details": {
                name: {
                    "status": e.status,
                    "events_seen": e.events_seen,
                    "age_ms": e.age_ms,
                    "last_error": e.last_error,
                }
                for name, e in self._streams.items()
            },
        }

    def get_health(self) -> dict[str, Any]:
        """Full health dict for /api/tradehud/health endpoint."""
        eval_result = self.evaluate()
        return eval_result

    def get_stream_status(self, logical_name: str) -> str:
        """Get current status of a specific stream."""
        if logical_name in self._streams:
            return self._streams[logical_name].status
        return "unknown"
