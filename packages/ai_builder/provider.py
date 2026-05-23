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
            "name": "EMA RSI Pullback Draft",
            "status": "draft",
            "stage": "draft",
            "output": "signal_preview_only",
            "indicators": [
                {"type": "EMA", "input": "close", "period": 20},
                {"type": "RSI", "input": "close", "period": 14},
            ],
            "entry": {"all": [{"crossed_above": ["close", "EMA_20"]}]},
            "exit": {"all": [{"gt": ["RSI_14", 70]}]},
            "risk": {"max_position_size": 1.0},
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
