from __future__ import annotations

import sqlite3

from packages.runtime_events.service import RuntimeEventService
from packages.runtime_events.stream import DurableRuntimeEventStream, runtime_event_schema_statements
from services.api.routes.runtime_events import replay_runtime_events_payload, runtime_events_sse_payload


def test_durable_runtime_stream_replays_events_across_service_instances() -> None:
    connection = sqlite3.connect(":memory:")
    stream = DurableRuntimeEventStream(connection=connection)
    service = RuntimeEventService(stream=stream)
    service.append_event(
        job_id="bt_001",
        stage="RUNNING",
        level="INFO",
        message="Processed 2025-03-01 to 2025-03-15",
        progress_pct=52.4,
    )

    reloaded = RuntimeEventService(stream=DurableRuntimeEventStream(connection=connection))

    assert reloaded.replay_events("bt_001")[0].message == "Processed 2025-03-01 to 2025-03-15"


def test_runtime_event_schema_creates_durable_event_table() -> None:
    connection = sqlite3.connect(":memory:")

    for statement in runtime_event_schema_statements(schema="builder"):
        connection.execute(statement)

    names = {row[0] for row in connection.execute("select name from sqlite_master where type = 'table'").fetchall()}
    assert "builder_runtime_events" in names


def test_replay_endpoint_reads_injected_durable_stream() -> None:
    connection = sqlite3.connect(":memory:")
    stream = DurableRuntimeEventStream(connection=connection)
    RuntimeEventService(stream=stream).append_event(
        job_id="bt_001",
        stage="RUNNING",
        level="INFO",
        message="persisted",
        progress_pct=1.0,
    )

    payload = replay_runtime_events_payload(service=RuntimeEventService(stream=stream), job_id="bt_001")

    assert payload[0]["job_id"] == "bt_001"
    assert payload[0]["stage"] == "RUNNING"
    assert payload[0]["level"] == "INFO"
    assert payload[0]["message"] == "persisted"
    assert payload[0]["progress_pct"] == 1.0
    assert payload[0]["event_id"] == "bt_001_evt_000001"
    assert payload[0]["actor_type"] == "system"
    assert payload[0]["metadata"]["progress_pct"] == 1.0


def test_runtime_events_sse_payload_is_observational_only() -> None:
    service = RuntimeEventService()
    service.append_event(job_id="bt_001", stage="RUNNING", level="INFO", message="hello", progress_pct=10.0)

    payload = runtime_events_sse_payload(service=service, job_id="bt_001")

    assert payload[0].startswith("event: runtime_event\n")
    assert '"job_id":"bt_001"' in payload[0]
