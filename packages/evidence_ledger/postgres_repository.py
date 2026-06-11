"""Evidence PostgreSQL repository — Segment I v4.

Persistent storage for evidence refs with project scoping.
"""
from __future__ import annotations

from typing import Any

from packages.evidence_ledger.models import EvidenceRef, EvidenceVerificationStatus
from packages.postgres.identifiers import safe_storage_identifier


class PostgresEvidenceRepository:
    """Postgres-backed evidence reference storage."""

    def __init__(self, conn: Any, schema: str = "builder") -> None:
        self._conn = conn
        self._schema = safe_storage_identifier(schema)
        self._ensure_table()

    def _ensure_table(self) -> None:
        """Create evidence_refs table if not exists."""
        self._conn.execute(f"""
            CREATE TABLE IF NOT EXISTS {self._schema}.evidence_refs (
                evidence_id TEXT PRIMARY KEY,
                project_id TEXT NOT NULL,
                strategy_id TEXT,
                strategy_version_id TEXT,
                artifact_ref TEXT NOT NULL,
                artifact_type TEXT NOT NULL,
                sha256 TEXT NOT NULL,
                schema_version TEXT NOT NULL,
                producer TEXT NOT NULL,
                created_at TEXT NOT NULL,
                expires_at TEXT,
                verification_status TEXT NOT NULL DEFAULT 'unverified',
                verification_error TEXT,
                metadata JSONB DEFAULT '{{}}'::jsonb
            )
        """)
        self._conn.execute(f"""
            CREATE INDEX IF NOT EXISTS idx_evidence_project
            ON {self._schema}.evidence_refs (project_id)
        """)

    def save(self, ref: EvidenceRef) -> None:
        """Insert or update an evidence ref."""
        self._conn.execute(
            f"""
            INSERT INTO {self._schema}.evidence_refs
                (evidence_id, project_id, strategy_id, strategy_version_id,
                 artifact_ref, artifact_type, sha256, schema_version,
                 producer, created_at, expires_at, verification_status,
                 verification_error, metadata)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14)
            ON CONFLICT (evidence_id) DO UPDATE SET
                verification_status = EXCLUDED.verification_status,
                verification_error = EXCLUDED.verification_error
            """,
            [
                ref.evidence_id, ref.project_id, ref.strategy_id,
                ref.strategy_version_id, ref.artifact_ref, ref.artifact_type,
                ref.sha256, ref.schema_version, ref.producer, ref.created_at,
                ref.expires_at, ref.verification_status, ref.verification_error,
                ref.metadata,
            ],
        )

    def get(self, evidence_id: str, project_id: str) -> EvidenceRef | None:
        """Get an evidence ref by ID, scoped to project."""
        row = self._conn.execute(
            f"""
            SELECT evidence_id, project_id, strategy_id, strategy_version_id,
                   artifact_ref, artifact_type, sha256, schema_version,
                   producer, created_at, expires_at, verification_status,
                   verification_error, metadata
            FROM {self._schema}.evidence_refs
            WHERE evidence_id = $1 AND project_id = $2
            """,
            [evidence_id, project_id],
        ).fetchone()
        if row is None:
            return None
        return self._row_to_ref(row)

    def list_by_project(self, project_id: str) -> list[EvidenceRef]:
        """List all evidence refs for a project."""
        rows = self._conn.execute(
            f"""
            SELECT evidence_id, project_id, strategy_id, strategy_version_id,
                   artifact_ref, artifact_type, sha256, schema_version,
                   producer, created_at, expires_at, verification_status,
                   verification_error, metadata
            FROM {self._schema}.evidence_refs
            WHERE project_id = $1
            ORDER BY created_at DESC
            """,
            [project_id],
        ).fetchall()
        return [self._row_to_ref(row) for row in rows]

    def update_status(
        self,
        evidence_id: str,
        project_id: str,
        status: EvidenceVerificationStatus,
        error: str | None = None,
    ) -> bool:
        """Update verification status. Returns True if updated."""
        result = self._conn.execute(
            f"""
            UPDATE {self._schema}.evidence_refs
            SET verification_status = $1, verification_error = $2
            WHERE evidence_id = $3 AND project_id = $4
            """,
            [status, error, evidence_id, project_id],
        )
        return result.rowcount > 0

    @staticmethod
    def _row_to_ref(row: tuple) -> EvidenceRef:
        return EvidenceRef(
            evidence_id=row[0],
            project_id=row[1],
            strategy_id=row[2],
            strategy_version_id=row[3],
            artifact_ref=row[4],
            artifact_type=row[5],
            sha256=row[6],
            schema_version=row[7],
            producer=row[8],
            created_at=row[9],
            expires_at=row[10],
            verification_status=row[11],
            verification_error=row[12],
            metadata=row[13] if isinstance(row[13], dict) else {},
        )
