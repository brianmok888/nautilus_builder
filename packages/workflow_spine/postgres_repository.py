from __future__ import annotations

import json
from sqlite3 import Connection

from packages.workflow_spine.storage_config import safe_storage_identifier
from packages.workflow_spine.models import (
    AiSuggestionRecord,
    StrategyIdentity,
    StrategyVersionIdentity,
    TestJobRecord,
    TestResultRecord,
)


def _table(schema: str, name: str) -> str:
    return f"{safe_storage_identifier(schema)}_{safe_storage_identifier(name)}"


def workflow_schema_statements(*, schema: str) -> list[str]:
    return [
        f"""
        create table if not exists {_table(schema, "strategy_identities")} (
            strategy_id text primary key,
            payload text not null
        )
        """,
        f"""
        create table if not exists {_table(schema, "strategy_versions")} (
            strategy_version_id text primary key,
            strategy_id text not null,
            strategy_lineage_id text not null,
            payload text not null
        )
        """,
        f"""
        create table if not exists {_table(schema, "test_jobs")} (
            test_job_id text primary key,
            strategy_version_id text not null,
            strategy_lineage_id text not null,
            payload text not null
        )
        """,
        f"""
        create table if not exists {_table(schema, "test_results")} (
            result_id text primary key,
            test_job_id text not null,
            strategy_lineage_id text not null,
            payload text not null
        )
        """,
        f"""
        create table if not exists {_table(schema, "ai_suggestions")} (
            suggestion_id text primary key,
            result_id text not null,
            strategy_lineage_id text not null,
            ai_thread_id text not null,
            payload text not null
        )
        """,
    ]


class PostgresWorkflowRepository:
    def __init__(self, *, connection: Connection, schema: str = "builder") -> None:
        self._connection = connection
        self._schema = safe_storage_identifier(schema)
        for statement in workflow_schema_statements(schema=schema):
            self._connection.execute(statement)
        self._connection.commit()

    def save_strategy(self, strategy: StrategyIdentity) -> None:
        self._upsert(
            "strategy_identities",
            "strategy_id",
            strategy.strategy_id,
            strategy.model_dump(mode="json"),
        )

    def save_version(self, version: StrategyVersionIdentity) -> None:
        self._connection.execute(
            f"""
            insert or replace into {_table(self._schema, "strategy_versions")}
            (strategy_version_id, strategy_id, strategy_lineage_id, payload)
            values (?, ?, ?, ?)
            """,
            (version.strategy_version_id, version.strategy_id, version.strategy_lineage_id, self._json(version.model_dump(mode="json"))),
        )
        self._connection.commit()

    def save_job(self, job: TestJobRecord) -> None:
        self._connection.execute(
            f"""
            insert or replace into {_table(self._schema, "test_jobs")}
            (test_job_id, strategy_version_id, strategy_lineage_id, payload)
            values (?, ?, ?, ?)
            """,
            (job.test_job_id, job.strategy_version_id, job.strategy_lineage_id, self._json(job.model_dump(mode="json"))),
        )
        self._connection.commit()

    def save_result(self, result: TestResultRecord) -> None:
        self._connection.execute(
            f"""
            insert or replace into {_table(self._schema, "test_results")}
            (result_id, test_job_id, strategy_lineage_id, payload)
            values (?, ?, ?, ?)
            """,
            (result.result_id, result.test_job_id, result.strategy_lineage_id, self._json(result.model_dump(mode="json"))),
        )
        self._connection.commit()

    def save_ai_suggestion(self, suggestion: AiSuggestionRecord) -> None:
        self._connection.execute(
            f"""
            insert or replace into {_table(self._schema, "ai_suggestions")}
            (suggestion_id, result_id, strategy_lineage_id, ai_thread_id, payload)
            values (?, ?, ?, ?, ?)
            """,
            (
                suggestion.suggestion_id,
                suggestion.result_id,
                suggestion.strategy_lineage_id,
                suggestion.ai_thread_id,
                self._json(suggestion.model_dump(mode="json")),
            ),
        )
        self._connection.commit()

    def strategy(self, strategy_id: str) -> StrategyIdentity | None:
        payload = self._fetch_payload("strategy_identities", "strategy_id", strategy_id)
        return StrategyIdentity(**payload) if payload else None

    def version(self, strategy_version_id: str) -> StrategyVersionIdentity | None:
        payload = self._fetch_payload("strategy_versions", "strategy_version_id", strategy_version_id)
        return StrategyVersionIdentity(**payload) if payload else None

    def job(self, test_job_id: str) -> TestJobRecord | None:
        payload = self._fetch_payload("test_jobs", "test_job_id", test_job_id)
        return TestJobRecord(**payload) if payload else None

    def result(self, result_id: str) -> TestResultRecord | None:
        payload = self._fetch_payload("test_results", "result_id", result_id)
        return TestResultRecord(**payload) if payload else None

    def suggestions_for_lineage(self, strategy_lineage_id: str) -> list[AiSuggestionRecord]:
        return self._fetch_suggestions("strategy_lineage_id", strategy_lineage_id)

    def suggestions_for_result(self, result_id: str) -> list[AiSuggestionRecord]:
        return self._fetch_suggestions("result_id", result_id)

    def suggestions_for_ai_thread(self, ai_thread_id: str) -> list[AiSuggestionRecord]:
        return self._fetch_suggestions("ai_thread_id", ai_thread_id)

    def _upsert(self, table: str, key_name: str, key_value: str, payload: dict[str, object]) -> None:
        self._connection.execute(
            f"insert or replace into {_table(self._schema, table)} ({key_name}, payload) values (?, ?)",
            (key_value, self._json(payload)),
        )
        self._connection.commit()

    def _fetch_payload(self, table: str, key_name: str, key_value: str) -> dict[str, object] | None:
        row = self._connection.execute(
            f"select payload from {_table(self._schema, table)} where {key_name} = ?",
            (key_value,),
        ).fetchone()
        return json.loads(row[0]) if row else None

    def _fetch_suggestions(self, key_name: str, key_value: str) -> list[AiSuggestionRecord]:
        rows = self._connection.execute(
            f"select payload from {_table(self._schema, "ai_suggestions")} where {key_name} = ? order by suggestion_id",
            (key_value,),
        ).fetchall()
        return [AiSuggestionRecord(**json.loads(row[0])) for row in rows]

    @staticmethod
    def _json(payload: dict[str, object]) -> str:
        return json.dumps(payload, sort_keys=True, separators=(",", ":"))
