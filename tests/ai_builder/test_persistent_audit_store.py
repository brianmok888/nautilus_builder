from __future__ import annotations

import sqlite3

from packages.ai_builder.provider import SqliteAiDraftAuditStore
from packages.ai_builder.service import AiBuilderService


def test_ai_draft_audit_records_persist_across_store_instances() -> None:
    connection = sqlite3.connect(":memory:")
    store = SqliteAiDraftAuditStore(connection=connection)
    service = AiBuilderService(store=store)

    service.generate_draft("Create EMA RSI", ai_thread_id="thread_001")
    reloaded = SqliteAiDraftAuditStore(connection=connection)

    records = reloaded.records_for_thread("thread_001")
    assert records[0]["mode"] == "advisory_only"
    assert records[0]["stage"] == "draft"
    assert records[0]["accepted"] is True
