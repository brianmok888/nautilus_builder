from __future__ import annotations

import json
from sqlite3 import Connection

from packages.runtime_events.models import RuntimeEvent
from packages.workflow_spine.storage_config import safe_storage_identifier


def runtime_event_schema_statements(*, schema: str) -> list[str]:
    safe_schema = safe_storage_identifier(schema)
    return [
        f"""
        create table if not exists {safe_schema}_runtime_events (
            sequence integer primary key autoincrement,
            job_id text not null,
            payload text not null
        )
        """
    ]


class InMemoryRuntimeEventStream:
    def __init__(self) -> None:
        self._events: dict[str, list[RuntimeEvent]] = {}

    def append(self, event: RuntimeEvent) -> None:
        self._events.setdefault(event.job_id, []).append(event)

    def replay(self, job_id: str) -> list[RuntimeEvent]:
        return list(self._events.get(job_id, []))


class DurableRuntimeEventStream:
    def __init__(self, *, connection: Connection, schema: str = "builder") -> None:
        self._connection = connection
        self._schema = safe_storage_identifier(schema)
        for statement in runtime_event_schema_statements(schema=schema):
            self._connection.execute(statement)
        self._connection.commit()

    def append(self, event: RuntimeEvent) -> None:
        self._connection.execute(
            f"insert into {self._schema}_runtime_events (job_id, payload) values (?, ?)",
            (event.job_id, json.dumps(event.model_dump(mode="json"), sort_keys=True, separators=(",", ":"))),
        )
        self._connection.commit()

    def replay(self, job_id: str) -> list[RuntimeEvent]:
        rows = self._connection.execute(
            f"select payload from {self._schema}_runtime_events where job_id = ? order by sequence",
            (job_id,),
        ).fetchall()
        return [RuntimeEvent(**json.loads(row[0])) for row in rows]
