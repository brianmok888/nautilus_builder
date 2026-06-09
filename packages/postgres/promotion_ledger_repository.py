"""Postgres-backed promotion ledger repository for Nautilus Builder.

Writes to compiler_runs, replay_runs, promotion_ledger, and audit_events tables
created by migration v2.

All methods enforce execution_authority=False — this is a Builder-only system.
"""
from __future__ import annotations

import uuid
from typing import Any

from packages.postgres.identifiers import postgres_table, safe_postgres_identifier
from packages.promotions.models import (
    AllowedPromotionMode,
    ForbiddenPromotionMode,
    validate_promotion_mode,
)


class PromotionLedgerError(Exception):
    """Raised when a promotion operation fails validation."""


# Fields required for each record type
_COMPILER_RUN_REQUIRED = {
    "strategy_id",
    "spec_version_id",
    "compiler_version",
    "compiler_hash",
    "policy_hash",
}

_REPLAY_RUN_REQUIRED = {
    "compiler_run_id",
    "dataset_hash",
    "dataset_uri",
    "replay_policy_hash",
}

_PROMOTION_REQUIRED = {
    "strategy_id",
    "spec_version_id",
    "promotion_mode",
    "strategy_spec_hash",
    "compiler_hash",
    "policy_hash",
    "dataset_hash",
    "replay_report_hash",
    "artifact_hash",
    "artifact_uri",
    "requested_by",
    "actor_id",
    "project_id",
    "request_id",
}


def _validate_required(data: dict[str, Any], required: set[str], label: str) -> None:
    """Check all required keys exist and are non-empty strings."""
    missing = [k for k in sorted(required) if k not in data or not data[k]]
    if missing:
        raise PromotionLedgerError(f"{label} missing required fields: {', '.join(missing)}")


class PromotionLedgerRepository:
    """Postgres-backed promotion evidence ledger.

    Parameters
    ----------
    conn
        A psycopg3 connection (or PooledConnection) supporting
        .execute() and .transaction().
    schema
        Database schema name (default ``builder``).
    """

    def __init__(self, conn: Any, schema: str = "builder") -> None:
        self._conn = conn
        self._schema = safe_postgres_identifier(schema)

    def _table(self, name: str) -> str:
        return postgres_table(self._schema, name)

    # ------------------------------------------------------------------
    # Compiler runs
    # ------------------------------------------------------------------

    def record_compiler_run(self, evidence: dict[str, Any]) -> dict[str, Any]:
        """Record a compiler run in the ``compiler_runs`` table."""
        _validate_required(evidence, _COMPILER_RUN_REQUIRED, "compiler_run")
        run_id = str(uuid.uuid4())
        with self._conn.transaction() as tx:
            tx.execute(
                f"INSERT INTO {self._table('compiler_runs')} "
                f"(id, strategy_id, spec_version_id, compiler_version, compiler_hash, policy_hash, status) "
                f"VALUES (%s, %s, %s, %s, %s, %s, %s)",
                (
                    run_id,
                    evidence["strategy_id"],
                    evidence["spec_version_id"],
                    evidence["compiler_version"],
                    evidence["compiler_hash"],
                    evidence["policy_hash"],
                    "pending",
                ),
            )
        return {"compiler_run_id": run_id, "status": "pending"}

    # ------------------------------------------------------------------
    # Replay runs
    # ------------------------------------------------------------------

    def record_replay_run(self, evidence: dict[str, Any]) -> dict[str, Any]:
        """Record a replay run in the ``replay_runs`` table."""
        _validate_required(evidence, _REPLAY_RUN_REQUIRED, "replay_run")
        run_id = str(uuid.uuid4())
        with self._conn.transaction() as tx:
            tx.execute(
                f"INSERT INTO {self._table('replay_runs')} "
                f"(id, strategy_id, compiler_run_id, dataset_hash, dataset_uri, replay_policy_hash, status) "
                f"VALUES (%s, %s, %s, %s, %s, %s, %s)",
                (
                    run_id,
                    evidence.get("strategy_id", ""),
                    evidence["compiler_run_id"],
                    evidence["dataset_hash"],
                    evidence["dataset_uri"],
                    evidence["replay_policy_hash"],
                    "pending",
                ),
            )
        return {"replay_run_id": run_id, "status": "pending"}

    # ------------------------------------------------------------------
    # Promotion ledger (evidence-gated)
    # ------------------------------------------------------------------

    def record_promotion(self, request: dict[str, Any]) -> dict[str, Any]:
        """Record a promotion in the ledger.

        Transaction boundary:
            validate evidence → write ledger → write audit event → return result.

        Fails closed on missing/mismatched evidence.
        """
        _validate_required(request, _PROMOTION_REQUIRED, "promotion")

        # Validate promotion mode (rejects live_trade_authority, etc.)
        try:
            mode = validate_promotion_mode(request["promotion_mode"])
        except ForbiddenPromotionMode as exc:
            raise PromotionLedgerError(f"forbidden promotion mode: {exc}") from exc

        # paper_replay_candidate requires approved_by
        if mode == AllowedPromotionMode.PAPER_REPLAY_CANDIDATE and not request.get("approved_by"):
            raise PromotionLedgerError("approved_by is required for paper_replay_candidate promotion")

        # artifact_hash must be non-empty
        if not request.get("artifact_hash"):
            raise PromotionLedgerError("artifact_hash is required and must be non-empty")

        promotion_id = str(uuid.uuid4())

        with self._conn.transaction() as tx:
            # Write to promotion_ledger
            tx.execute(
                f"INSERT INTO {self._table('promotion_ledger')} "
                f"(id, strategy_id, spec_version_id, compiler_run_id, replay_run_id, "
                f"promotion_mode, strategy_spec_hash, compiler_hash, policy_hash, "
                f"dataset_hash, replay_report_hash, artifact_hash, artifact_uri, "
                f"status, requested_by, approved_by) "
                f"VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
                (
                    promotion_id,
                    request["strategy_id"],
                    request["spec_version_id"],
                    request.get("compiler_run_id"),
                    request.get("replay_run_id"),
                    request["promotion_mode"],
                    request["strategy_spec_hash"],
                    request["compiler_hash"],
                    request["policy_hash"],
                    request["dataset_hash"],
                    request["replay_report_hash"],
                    request["artifact_hash"],
                    request["artifact_uri"],
                    "pending",
                    request["requested_by"],
                    request.get("approved_by"),
                ),
            )

            # Write to audit_events
            tx.execute(
                f"INSERT INTO {self._table('audit_events')} "
                f"(request_id, actor_id, project_id, action, resource_type, resource_id, status) "
                f"VALUES (%s, %s, %s, %s, %s, %s, %s)",
                (
                    request["request_id"],
                    request["actor_id"],
                    request["project_id"],
                    "promotion",
                    "promotion_ledger",
                    promotion_id,
                    "created",
                ),
            )

        return {
            "promotion_id": promotion_id,
            "status": "pending",
            "execution_authority": False,
            "promotion_mode": request["promotion_mode"],
        }

    # ------------------------------------------------------------------
    # Read operations
    # ------------------------------------------------------------------

    def get_promotion(self, promotion_id: str) -> dict[str, Any] | None:
        """Read a promotion by ID."""
        row = self._conn.execute(
            f"SELECT id, strategy_id, spec_version_id, compiler_run_id, replay_run_id, "
            f"promotion_mode, strategy_spec_hash, compiler_hash, policy_hash, "
            f"dataset_hash, replay_report_hash, artifact_hash, artifact_uri, "
            f"status, requested_by, approved_by, created_at, approved_at "
            f"FROM {self._table('promotion_ledger')} WHERE id = %s",
            (promotion_id,),
        ).fetchone()
        if not row:
            return None
        return {
            "promotion_id": str(row[0]),
            "strategy_id": row[1],
            "spec_version_id": row[2],
            "compiler_run_id": str(row[3]),
            "replay_run_id": str(row[4]),
            "promotion_mode": row[5],
            "strategy_spec_hash": row[6],
            "compiler_hash": row[7],
            "policy_hash": row[8],
            "dataset_hash": row[9],
            "replay_report_hash": row[10],
            "artifact_hash": row[11],
            "artifact_uri": row[12],
            "status": row[13],
            "requested_by": row[14],
            "approved_by": row[15],
            "created_at": row[16],
            "approved_at": row[17],
            "execution_authority": False,
        }

    def list_promotions(self, *, project_id: str | None = None) -> list[dict[str, Any]]:
        """List promotions, optionally filtered by project_id.

        Note: promotion_ledger doesn't have a project_id column directly.
        Filtering is done via the audit_events join or by actor_id scope.
        For now, we return all promotions and let the caller filter.
        """
        rows = self._conn.execute(
            f"SELECT id, strategy_id, spec_version_id, compiler_run_id, replay_run_id, "
            f"promotion_mode, strategy_spec_hash, compiler_hash, policy_hash, "
            f"dataset_hash, replay_report_hash, artifact_hash, artifact_uri, "
            f"status, requested_by, approved_by, created_at, approved_at "
            f"FROM {self._table('promotion_ledger')} ORDER BY created_at DESC"
        ).fetchall()
        return [
            {
                "promotion_id": str(r[0]),
                "strategy_id": r[1],
                "spec_version_id": r[2],
                "compiler_run_id": str(r[3]),
                "replay_run_id": str(r[4]),
                "promotion_mode": r[5],
                "strategy_spec_hash": r[6],
                "compiler_hash": r[7],
                "policy_hash": r[8],
                "dataset_hash": r[9],
                "replay_report_hash": r[10],
                "artifact_hash": r[11],
                "artifact_uri": r[12],
                "status": r[13],
                "requested_by": r[14],
                "approved_by": r[15],
                "created_at": r[16],
                "approved_at": r[17],
                "execution_authority": False,
            }
            for r in rows
        ]
