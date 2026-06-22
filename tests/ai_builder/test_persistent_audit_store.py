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


def test_ai_draft_apply_payload_preserves_thread_cycle_and_lineage_ids() -> None:
    from packages.ai_builder.service import AiBuilderService

    result = AiBuilderService().apply_draft_to_strategy(
        prompt="Create EMA RSI",
        ai_thread_id="ai_thread_001",
        improvement_cycle_id="cycle_001",
        strategy_lineage_id="lineage_strategy_001",
        strategy_version_id="strategy_001_v002",
    )

    assert result["ai_thread_id"] == "ai_thread_001"
    assert result["improvement_cycle_id"] == "cycle_001"
    assert result["strategy_lineage_id"] == "lineage_strategy_001"
    assert result["strategy_version_id"] == "strategy_001_v002"
    assert result["stage"] == "draft"


def test_ai_draft_apply_rejects_blank_provenance_ids() -> None:
    import pytest

    with pytest.raises(ValueError, match="ai_thread_id is required"):
        AiBuilderService().apply_draft_to_strategy(
            prompt="Create EMA RSI",
            ai_thread_id="",
            improvement_cycle_id="cycle_001",
            strategy_lineage_id="lineage_strategy_001",
            strategy_version_id="strategy_001_v002",
        )


def test_ai_draft_apply_uses_supplied_spec_without_regenerating() -> None:
    class ExplodingProvider:
        def draft_spec(self, prompt: str) -> dict[str, object]:
            raise AssertionError(f"provider must not regenerate supplied draft: {prompt}")

    generated = AiBuilderService().generate_draft("Create EMA RSI", ai_thread_id="thread_source")

    result = AiBuilderService(provider=ExplodingProvider()).apply_draft_to_strategy(
        prompt="Create EMA RSI",
        ai_thread_id="ai_thread_001",
        improvement_cycle_id="cycle_001",
        strategy_lineage_id="lineage_strategy_001",
        strategy_version_id="strategy_001_v002",
        spec=generated.spec,
    )

    assert result["spec"] == generated.spec
