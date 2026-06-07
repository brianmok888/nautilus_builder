"""Tests for promotion_ledger_repository: Postgres-backed evidence ledger.

TDD RED phase — these tests define the required behavior BEFORE implementation.
The repository writes to compiler_runs, replay_runs, promotion_ledger, audit_events.
"""
from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any
from unittest.mock import MagicMock

import pytest

from packages.postgres.promotion_ledger_repository import (
    PromotionLedgerRepository,
    PromotionLedgerError,
)


# ---------------------------------------------------------------------------
# Helpers — lightweight mock connection that tracks SQL and returns rows
# ---------------------------------------------------------------------------

class FakeCursor:
    """Tracks executed SQL/params and returns pre-registered rows."""

    def __init__(self) -> None:
        self.executed: list[tuple[str, tuple | None]] = []
        self._next_rows: list[tuple | None] = []

    def execute(self, sql: str, params: tuple | None = None) -> "FakeCursor":
        self.executed.append((sql, params))
        return self

    def fetchone(self) -> tuple | None:
        if self._next_rows:
            return self._next_rows.pop(0)
        return None

    def fetchall(self) -> list[tuple]:
        if self._next_rows:
            rows = list(self._next_rows)
            self._next_rows.clear()
            return rows
        return []

    def set_next_row(self, row: tuple | None) -> None:
        self._next_rows.append(row)


class FakeTx:
    """Context manager yielding a FakeCursor."""

    def __init__(self) -> None:
        self.cursor = FakeCursor()

    def __enter__(self) -> FakeCursor:
        return self.cursor

    def __exit__(self, *args: object) -> None:
        pass

    def execute(self, sql: str, params: tuple | None = None) -> "FakeCursor":
        return self.cursor.execute(sql, params)

    def fetchone(self) -> tuple | None:
        return self.cursor.fetchone()


class FakeConn:
    """Mock Postgres connection with transaction support."""

    def __init__(self) -> None:
        self._transactions: list[FakeTx] = []
        self._current_tx: FakeTx | None = None

    def transaction(self) -> FakeTx:
        tx = FakeTx()
        self._transactions.append(tx)
        self._current_tx = tx
        return tx

    def execute(self, sql: str, params: tuple | None = None) -> FakeCursor:
        # For non-transaction queries, create a throwaway cursor
        c = FakeCursor()
        c.execute(sql, params)
        return c

    @property
    def last_tx(self) -> FakeTx | None:
        return self._transactions[-1] if self._transactions else None


# ---------------------------------------------------------------------------
# Test data helpers
# ---------------------------------------------------------------------------

def _compiler_evidence(
    *,
    strategy_id: str = "strat_001",
    spec_version_id: str = "strat_001_v001",
    compiler_hash: str = "sha256:abc123",
    policy_hash: str = "sha256:policy456",
    compiler_version: str = "1.0.0",
) -> dict[str, Any]:
    return {
        "strategy_id": strategy_id,
        "spec_version_id": spec_version_id,
        "compiler_version": compiler_version,
        "compiler_hash": compiler_hash,
        "policy_hash": policy_hash,
    }


def _replay_evidence(
    *,
    compiler_run_id: str = "00000000-0000-0000-0000-000000000001",
    dataset_hash: str = "sha256:dataset789",
    dataset_uri: str = "artifact://builder/proj/user/replay/test_run",
    replay_policy_hash: str = "sha256:replay_policy",
) -> dict[str, Any]:
    return {
        "compiler_run_id": compiler_run_id,
        "dataset_hash": dataset_hash,
        "dataset_uri": dataset_uri,
        "replay_policy_hash": replay_policy_hash,
    }


def _promotion_request(
    *,
    strategy_id: str = "strat_001",
    spec_version_id: str = "strat_001_v001",
    promotion_mode: str = "shadow_only",
    strategy_spec_hash: str = "sha256:spec123",
    compiler_hash: str = "sha256:abc123",
    policy_hash: str = "sha256:policy456",
    dataset_hash: str = "sha256:dataset789",
    replay_report_hash: str = "sha256:report012",
    artifact_hash: str = "sha256:artifact345",
    artifact_uri: str = "s3://bucket/artifacts/shadow_only/sha256/345/artifact.json",
    requested_by: str = "user_001",
    approved_by: str | None = None,
    actor_id: str = "user_001",
    project_id: str = "proj_001",
    request_id: str = "req_001",
) -> dict[str, Any]:
    return {
        "strategy_id": strategy_id,
        "spec_version_id": spec_version_id,
        "promotion_mode": promotion_mode,
        "strategy_spec_hash": strategy_spec_hash,
        "compiler_hash": compiler_hash,
        "policy_hash": policy_hash,
        "dataset_hash": dataset_hash,
        "replay_report_hash": replay_report_hash,
        "artifact_hash": artifact_hash,
        "artifact_uri": artifact_uri,
        "requested_by": requested_by,
        "approved_by": approved_by,
        "actor_id": actor_id,
        "project_id": project_id,
        "request_id": request_id,
    }


# ===========================================================================
# P1-1 Tests: record_compiler_run
# ===========================================================================

class TestRecordCompilerRun:
    def test_writes_to_compiler_runs_table(self):
        conn = FakeConn()
        repo = PromotionLedgerRepository(conn)
        evidence = _compiler_evidence()

        result = repo.record_compiler_run(evidence)

        assert result is not None
        assert "compiler_run_id" in result
        tx = conn.last_tx
        assert tx is not None
        sqls = [s for s, _ in tx.cursor.executed]
        assert any("compiler_runs" in s for s in sqls)

    def test_returns_compiler_run_id_and_status(self):
        conn = FakeConn()
        repo = PromotionLedgerRepository(conn)

        result = repo.record_compiler_run(_compiler_evidence())

        assert result["status"] == "pending"
        assert result["compiler_run_id"] is not None

    def test_missing_strategy_id_raises(self):
        conn = FakeConn()
        repo = PromotionLedgerRepository(conn)
        evidence = _compiler_evidence()
        del evidence["strategy_id"]

        with pytest.raises(PromotionLedgerError, match="strategy_id"):
            repo.record_compiler_run(evidence)

    def test_missing_compiler_hash_raises(self):
        conn = FakeConn()
        repo = PromotionLedgerRepository(conn)
        evidence = _compiler_evidence()
        del evidence["compiler_hash"]

        with pytest.raises(PromotionLedgerError, match="compiler_hash"):
            repo.record_compiler_run(evidence)


# ===========================================================================
# P1-1 Tests: record_replay_run
# ===========================================================================

class TestRecordReplayRun:
    def test_writes_to_replay_runs_table(self):
        conn = FakeConn()
        repo = PromotionLedgerRepository(conn)

        result = repo.record_replay_run(_replay_evidence())

        assert result is not None
        assert "replay_run_id" in result
        tx = conn.last_tx
        assert tx is not None
        sqls = [s for s, _ in tx.cursor.executed]
        assert any("replay_runs" in s for s in sqls)

    def test_returns_replay_run_id_and_status(self):
        conn = FakeConn()
        repo = PromotionLedgerRepository(conn)

        result = repo.record_replay_run(_replay_evidence())

        assert result["status"] == "pending"
        assert result["replay_run_id"] is not None

    def test_missing_compiler_run_id_raises(self):
        conn = FakeConn()
        repo = PromotionLedgerRepository(conn)
        evidence = _replay_evidence()
        del evidence["compiler_run_id"]

        with pytest.raises(PromotionLedgerError, match="compiler_run_id"):
            repo.record_replay_run(evidence)

    def test_missing_dataset_hash_raises(self):
        conn = FakeConn()
        repo = PromotionLedgerRepository(conn)
        evidence = _replay_evidence()
        del evidence["dataset_hash"]

        with pytest.raises(PromotionLedgerError, match="dataset_hash"):
            repo.record_replay_run(evidence)


# ===========================================================================
# P1-1 Tests: record_promotion (the main evidence-gated promotion path)
# ===========================================================================

class TestRecordPromotion:
    """Promotion must fail closed on missing/mismatched evidence.

    Transaction boundary: validate evidence -> write ledger -> write audit -> return.
    """

    def test_missing_compiler_evidence_fails(self):
        """Promotion fails if compiler_run_id is missing."""
        conn = FakeConn()
        repo = PromotionLedgerRepository(conn)
        req = _promotion_request()
        del req["compiler_hash"]

        with pytest.raises(PromotionLedgerError, match="compiler"):
            repo.record_promotion(req)

    def test_missing_replay_evidence_fails(self):
        """Promotion fails if dataset_hash or replay_report_hash is missing."""
        conn = FakeConn()
        repo = PromotionLedgerRepository(conn)
        req = _promotion_request()
        del req["dataset_hash"]

        with pytest.raises(PromotionLedgerError, match="dataset_hash"):
            repo.record_promotion(req)

    def test_missing_replay_report_hash_fails(self):
        conn = FakeConn()
        repo = PromotionLedgerRepository(conn)
        req = _promotion_request()
        del req["replay_report_hash"]

        with pytest.raises(PromotionLedgerError, match="replay_report_hash"):
            repo.record_promotion(req)

    def test_mismatched_artifact_hash_fails(self):
        """Promotion fails if artifact_hash is empty or missing."""
        conn = FakeConn()
        repo = PromotionLedgerRepository(conn)
        req = _promotion_request(artifact_hash="")

        with pytest.raises(PromotionLedgerError, match="artifact_hash"):
            repo.record_promotion(req)

    def test_missing_approver_for_final_promotion_fails(self):
        """Final/promotion that requires manual approval fails without approver."""
        conn = FakeConn()
        repo = PromotionLedgerRepository(conn)
        # paper_replay_candidate requires approved_by
        req = _promotion_request(
            promotion_mode="paper_replay_candidate",
            approved_by=None,
        )

        with pytest.raises(PromotionLedgerError, match="approved_by"):
            repo.record_promotion(req)

    def test_unsupported_promotion_mode_fails(self):
        """Forbidden modes (live_trade_authority) are rejected."""
        conn = FakeConn()
        repo = PromotionLedgerRepository(conn)
        req = _promotion_request(promotion_mode="live_trade_authority")

        with pytest.raises(PromotionLedgerError, match="forbidden"):
            repo.record_promotion(req)

    def test_successful_promotion_writes_ledger_and_audit(self):
        """Happy path: promotion writes to both promotion_ledger and audit_events."""
        conn = FakeConn()
        repo = PromotionLedgerRepository(conn)
        req = _promotion_request()

        result = repo.record_promotion(req)

        assert result is not None
        assert "promotion_id" in result
        assert result["status"] == "pending"
        assert result["execution_authority"] is False

        # Verify both tables were written within the transaction
        tx = conn.last_tx
        assert tx is not None
        sqls = [s for s, _ in tx.cursor.executed]
        assert any("promotion_ledger" in s for s in sqls)
        assert any("audit_events" in s for s in sqls)

    def test_promotion_enforces_execution_authority_false(self):
        """All promotion results must have execution_authority=False."""
        conn = FakeConn()
        repo = PromotionLedgerRepository(conn)
        req = _promotion_request()

        result = repo.record_promotion(req)

        assert result["execution_authority"] is False


# ===========================================================================
# P1-1 Tests: get_promotion / list_promotions
# ===========================================================================

class TestGetPromotion:
    def test_get_promotion_returns_record(self):
        conn = FakeConn()
        repo = PromotionLedgerRepository(conn)
        promo_id = str(uuid.uuid4())
        # Simulate DB returning a row
        conn.execute = MagicMock(return_value=FakeCursor())
        conn.execute.return_value.set_next_row((
            promo_id, "strat_001", "strat_001_v001",
            "00000000-0000-0000-0000-000000000001",
            "00000000-0000-0000-0000-000000000002",
            "shadow_only", "sha256:spec123", "sha256:abc123",
            "sha256:policy456", "sha256:dataset789", "sha256:report012",
            "sha256:artifact345", "s3://bucket/art", "pending",
            "user_001", None, datetime.now(UTC), None,
        ))

        result = repo.get_promotion(promo_id)

        assert result is not None
        assert result["promotion_id"] == promo_id
        assert result["execution_authority"] is False

    def test_get_promotion_returns_none_when_not_found(self):
        conn = FakeConn()
        repo = PromotionLedgerRepository(conn)
        conn.execute = MagicMock(return_value=FakeCursor())

        result = repo.get_promotion("nonexistent-id")

        assert result is None


class TestListPromotions:
    def test_list_promotions_by_project(self):
        conn = FakeConn()
        repo = PromotionLedgerRepository(conn)
        conn.execute = MagicMock(return_value=FakeCursor())

        repo.list_promotions(project_id="proj_001")  # returns empty list

        # Returns empty list (no rows) but did execute a query
        conn.execute.assert_called_once()
        sql = conn.execute.call_args[0][0]
        assert "promotion_ledger" in sql

    def test_list_promotions_returns_records(self):
        conn = FakeConn()
        repo = PromotionLedgerRepository(conn)
        c = FakeCursor()
        c.set_next_row((
            str(uuid.uuid4()), "strat_001", "strat_001_v001",
            "00000000-0000-0000-0000-000000000001",
            "00000000-0000-0000-0000-000000000002",
            "shadow_only", "sha256:spec", "sha256:comp",
            "sha256:pol", "sha256:data", "sha256:rep",
            "sha256:art", "s3://bucket/art", "pending",
            "user_001", None, datetime.now(UTC), None,
        ))
        conn.execute = MagicMock(return_value=c)

        result = repo.list_promotions(project_id="proj_001")  # returns empty list

        assert len(result) == 1
        assert result[0]["execution_authority"] is False
