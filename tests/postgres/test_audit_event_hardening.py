from __future__ import annotations

import pytest


class CapturingConnection:
    def __init__(self) -> None:
        self.executed: list[tuple[str, tuple[object, ...]]] = []

    def execute(self, sql: str, params: tuple[object, ...]) -> None:
        self.executed.append((sql, params))


class FailingConnection:
    def execute(self, sql: str, params: tuple[object, ...]) -> None:
        raise RuntimeError("audit insert failed")


def test_fastapi_postgres_audit_writer_persists_project_id() -> None:
    from services.api.fastapi_app import _build_audit_writer

    conn = CapturingConnection()
    writer = _build_audit_writer(conn)

    writer(
        {
            "request_id": "req_001",
            "actor_id": "user_123",
            "project_id": "project_alpha",
            "method": "POST",
            "route": "/api/strategies",
            "resource_type": "strategies",
            "resource_id": "strategy_001",
            "status_code": 201,
            "created_at": "2026-06-08T00:00:00+00:00",
        }
    )

    sql, params = conn.executed[0]
    assert "project_id" in sql
    assert params[2] == "project_alpha"


def test_fastapi_postgres_audit_writer_propagates_insert_failure() -> None:
    from services.api.fastapi_app import _build_audit_writer

    writer = _build_audit_writer(FailingConnection())

    with pytest.raises(RuntimeError, match="audit insert failed"):
        writer(
            {
                "request_id": "req_001",
                "actor_id": "user_123",
                "project_id": "project_alpha",
                "method": "POST",
                "route": "/api/strategies",
                "resource_type": "strategies",
                "status_code": 201,
                "created_at": "2026-06-08T00:00:00+00:00",
            }
        )


def test_audit_event_migrations_make_project_id_non_null_with_default() -> None:
    from packages.postgres.migrations import MIGRATIONS

    v6 = next(migration for migration in MIGRATIONS if migration.version == 6)

    assert "audit_events" in v6.up
    assert "project_id" in v6.up
    assert "SET NOT NULL" in v6.up
    assert "DEFAULT 'unknown'" in v6.up


def test_promotion_ledger_audit_write_includes_project_id() -> None:
    from packages.postgres.promotion_ledger_repository import PromotionLedgerRepository
    from tests.postgres.test_promotion_ledger_repository import FakeConn, _promotion_request

    conn = FakeConn()
    repo = PromotionLedgerRepository(conn)
    request = _promotion_request(project_id="project_alpha")

    repo.record_promotion(request)

    tx = conn.last_tx
    assert tx is not None
    audit_sql, audit_params = next(
        (sql, params)
        for sql, params in tx.cursor.executed
        if "audit_events" in sql
    )
    assert "project_id" in audit_sql
    assert "project_alpha" in audit_params
