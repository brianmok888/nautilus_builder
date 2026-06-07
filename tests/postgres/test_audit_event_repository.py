"""Tests for Postgres audit event repository and audit writer factory.

Uses synchronous mocks since the test suite does not have pytest-asyncio.
The async repository methods are tested via asyncio.run() helpers.
"""
from __future__ import annotations

import asyncio

import pytest

from packages.postgres.audit_event_repository import (
    PostgresAuditEventRepository,
    make_audit_writer_from_pool,
)


class MockPool:
    """Mock asyncpg pool for testing."""

    def __init__(self) -> None:
        self.events: list[dict] = []

    class _AcquireContext:
        def __init__(self, pool: "MockPool") -> None:
            self._pool = pool

        async def __aenter__(self) -> "MockPool._AcquireContext":
            return self

        async def __aexit__(self, *args: object) -> None:
            pass

        async def execute(self, sql: str, *args: object) -> None:
            self._pool.events.append({"sql": sql, "args": args})

        async def fetch(self, sql: str, *args: object) -> list[dict]:
            return []

    def acquire(self) -> "MockPool._AcquireContext":
        return self._AcquireContext(self)


def _run(coro):
    """Run a coroutine in a fresh event loop."""
    return asyncio.new_event_loop().run_until_complete(coro)


# ---------------------------------------------------------------------------
# PostgresAuditEventRepository
# ---------------------------------------------------------------------------

class TestPostgresAuditEventRepository:
    def test_write_audit_event_with_pool(self):
        pool = MockPool()
        repo = PostgresAuditEventRepository(pool=pool)

        event_id = _run(repo.write_audit_event(
            request_id="req-001",
            actor_id="user-001",
            project_id="proj-001",
            action="strategy.create",
            resource_type="strategy",
            resource_id="strat-001",
            status="success",
        ))

        assert event_id is not None
        assert len(pool.events) == 1
        assert "INSERT INTO builder.audit_events" in pool.events[0]["sql"]

    def test_write_returns_none_without_pool(self):
        repo = PostgresAuditEventRepository(pool=None)
        event_id = _run(repo.write_audit_event(
            request_id="req-002",
            action="strategy.delete",
            resource_type="strategy",
        ))
        assert event_id is None

    def test_write_with_all_fields(self):
        pool = MockPool()
        repo = PostgresAuditEventRepository(pool=pool)

        event_id = _run(repo.write_audit_event(
            request_id="req-003",
            actor_id="user-002",
            project_id="proj-002",
            action="promotion.request",
            resource_type="promotion",
            resource_id="promo-001",
            before_hash="abc123",
            after_hash="def456",
            status="success",
            error_code=None,
        ))

        assert event_id is not None
        args = pool.events[0]["args"]
        assert args[1] == "req-003"
        assert args[2] == "user-002"
        assert args[3] == "proj-002"

    def test_write_failed_status(self):
        pool = MockPool()
        repo = PostgresAuditEventRepository(pool=pool)

        event_id = _run(repo.write_audit_event(
            request_id="req-004",
            action="strategy.compile",
            resource_type="strategy",
            status="failed",
            error_code="COMPILE_ERROR",
        ))

        assert event_id is not None

    def test_query_returns_empty_without_pool(self):
        repo = PostgresAuditEventRepository(pool=None)
        results = _run(repo.query_audit_events())
        assert results == []

    def test_query_with_pool_returns_list(self):
        pool = MockPool()
        repo = PostgresAuditEventRepository(pool=pool)
        results = _run(repo.query_audit_events(actor_id="user-001", limit=50))
        assert isinstance(results, list)

    def test_write_generates_unique_event_id(self):
        pool = MockPool()
        repo = PostgresAuditEventRepository(pool=pool)

        id1 = _run(repo.write_audit_event(
            request_id="req-005",
            action="test.action",
            resource_type="test",
        ))
        id2 = _run(repo.write_audit_event(
            request_id="req-006",
            action="test.action",
            resource_type="test",
        ))

        assert id1 != id2


# ---------------------------------------------------------------------------
# make_audit_writer_from_pool factory
# ---------------------------------------------------------------------------

class TestMakeAuditWriterFromPool:
    def test_factory_returns_callable(self):
        pool = MockPool()
        writer = make_audit_writer_from_pool(pool)
        assert callable(writer)

    def test_factory_without_pool_returns_callable(self):
        writer = make_audit_writer_from_pool(None)
        assert callable(writer)

    def test_writer_in_event_loop_schedules_task(self):
        """When called inside an event loop, writer schedules a task."""
        pool = MockPool()
        writer = make_audit_writer_from_pool(pool)

        async def _test():
            writer({
                "request_id": "req-007",
                "actor_id": "user-003",
                "project_id": "proj-003",
                "method": "POST",
                "route": "/api/strategies",
                "status_code": 201,
                "resource_type": "strategy",
                "resource_id": "strat-003",
            })
            await asyncio.sleep(0.01)
            assert len(pool.events) == 1

        asyncio.new_event_loop().run_until_complete(_test())

    def test_writer_outside_event_loop_logs_warning(self):
        """When called outside event loop, writer logs but does not raise."""
        pool = MockPool()
        writer = make_audit_writer_from_pool(pool)

        # Should not raise
        writer({"request_id": "req-008"})

    def test_writer_handles_empty_event(self):
        pool = MockPool()
        writer = make_audit_writer_from_pool(pool)

        # Should not raise
        writer({})


# ---------------------------------------------------------------------------
# Audit event schema validation
# ---------------------------------------------------------------------------

class TestAuditEventSchema:
    def test_audit_events_table_has_required_columns(self):
        from packages.postgres.migrations import MIGRATIONS

        v2_up = None
        v3_up = None
        for m in MIGRATIONS:
            if m.version == 2:
                v2_up = m.up
            if m.version == 3:
                v3_up = m.up

        assert v2_up is not None, "Migration v2 not found"
        assert v3_up is not None, "Migration v3 not found"

        required_columns = [
            "id", "request_id", "actor_id", "action",
            "resource_type", "resource_id", "before_hash", "after_hash",
            "status", "error_code", "created_at",
        ]
        for col in required_columns:
            assert col in v2_up, f"Column {col} missing from audit_events migration"

        assert "project_id" in v3_up

    def test_audit_events_has_indexes(self):
        from packages.postgres.migrations import MIGRATIONS

        v3_up = next(m.up for m in MIGRATIONS if m.version == 3)
        assert "idx_audit_events_project_id" in v3_up
        assert "idx_audit_events_actor_id" in v3_up
        assert "idx_audit_events_created_at" in v3_up
