from __future__ import annotations

import json
from sqlite3 import Connection
from typing import Protocol


class DraftProviderProtocol(Protocol):
    def draft_spec(self, prompt: str) -> dict[str, object]: ...


class DraftAuditStoreProtocol(Protocol):
    def save(self, record: dict[str, object]) -> None: ...


class AdvisoryDraftProvider:
    def draft_spec(self, prompt: str) -> dict[str, object]:
        return {
            "schema_version": "1.0.0",
            "version": "0.1.0-draft.1",
            "stage": "draft",
            "status": "draft",
            "created_from": "ai_builder",
            "is_frozen": False,
            "adapter_id": "BINANCE_PERP",
            "venue": "BINANCE",
            "instrument_id": "BTCUSDT-PERP",
            "bar_type": "BTCUSDT-PERP.BINANCE-5-MINUTE-LAST-EXTERNAL",
            "data_range": {
                "start": "2025-01-01T00:00:00Z",
                "end": "2025-06-01T00:00:00Z",
            },
            "indicators": {
                "ema_fast": {"type": "EMA", "input": "close", "period": 20},
                "ema_slow": {"type": "EMA", "input": "close", "period": 50},
                "rsi": {"type": "RSI", "input": "close", "period": 14},
            },
            "rules": {
                "long_entry": {
                    "all": [
                        {"crossed_above": ["ema_fast", "ema_slow"]},
                        {"gt": ["rsi", 52]},
                    ]
                },
                "long_exit": {
                    "any": [
                        {"crossed_below": ["ema_fast", "ema_slow"]},
                        {"lt": ["rsi", 45]},
                    ]
                },
            },
            "risk": {
                "position_size_pct": 0.05,
                "stop_loss_pct": 0.012,
                "take_profit_pct": 0.024,
                "max_hold_bars": 48,
            },
            "validation": {
                "bar_close_only": True,
                "no_lookahead_required": True,
                "requires_backtest_before_shadow": True,
                "output_mode": "signal_preview_only",
            },
            "provenance": {
                "created_by": "ai_builder",
                "parent_version_id": None,
            },
        }


class RecordedAiDraftStore:
    def __init__(self) -> None:
        self._records: list[dict[str, object]] = []

    def save(self, record: dict[str, object]) -> None:
        self._records.append(dict(record))

    def records_for_thread(self, ai_thread_id: str) -> list[dict[str, object]]:
        return [record for record in self._records if record["ai_thread_id"] == ai_thread_id]


class SqliteAiDraftAuditStore:
    def __init__(self, *, connection: Connection) -> None:
        self._connection = connection
        self._connection.execute(
            """
            create table if not exists builder_ai_draft_audit (
                sequence integer primary key autoincrement,
                ai_thread_id text not null,
                payload text not null
            )
            """
        )
        self._connection.commit()

    def save(self, record: dict[str, object]) -> None:
        self._connection.execute(
            "insert into builder_ai_draft_audit (ai_thread_id, payload) values (?, ?)",
            (str(record["ai_thread_id"]), json.dumps(record, sort_keys=True, separators=(",", ":"))),
        )
        self._connection.commit()

    def records_for_thread(self, ai_thread_id: str) -> list[dict[str, object]]:
        rows = self._connection.execute(
            "select payload from builder_ai_draft_audit where ai_thread_id = ? order by sequence",
            (ai_thread_id,),
        ).fetchall()
        return [json.loads(row[0]) for row in rows]
