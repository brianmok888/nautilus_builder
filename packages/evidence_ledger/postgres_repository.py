"""Evidence PostgreSQL repository — Segment 02 v5.

Persistent storage for evidence refs with project scoping.
Aligned with EvidenceRef model fields from models.py.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any

from packages.evidence_ledger.models import (
    ArtifactType,
    EvidenceRef,
    VerificationStatus,
)
from packages.postgres.identifiers import safe_postgres_identifier


class PostgresEvidenceRepository:
    """Postgres-backed evidence reference storage."""

    def __init__(self, conn: Any, schema: str = "builder") -> None:
        self._conn = conn
        self._schema = safe_postgres_identifier(schema)
        self._ensure_table()

    def _ensure_table(self) -> None:
        """Create evidence_refs table if not exists."""
        self._conn.execute(f"""
            CREATE TABLE IF NOT EXISTS {self._schema}.evidence_refs (
                evidence_id TEXT PRIMARY KEY,
                project_id TEXT NOT NULL,
                strategy_lineage_id TEXT,
                strategy_version_id TEXT,
                artifact_type TEXT NOT NULL,
                source_system TEXT NOT NULL,
                uri TEXT NOT NULL,
                sha256 TEXT NOT NULL DEFAULT '',
                schema_version TEXT NOT NULL DEFAULT 'evidence_v1',
                created_at TEXT,
                producer TEXT NOT NULL DEFAULT 'builder',
                status TEXT NOT NULL DEFAULT 'active',
                verification_status TEXT NOT NULL DEFAULT 'unverified',
                verification_error TEXT,
                expires_at TEXT,
                metadata JSONB DEFAULT '{{}}'::jsonb
            )
        """)
        self._conn.execute(f"""
            CREATE INDEX IF NOT EXISTS idx_evidence_project
            ON {self._schema}.evidence_refs (project_id)
        """)
        self._conn.execute(f"""
            CREATE INDEX IF NOT EXISTS idx_evidence_strategy_lineage
            ON {self._schema}.evidence_refs (project_id, strategy_lineage_id)
            WHERE strategy_lineage_id IS NOT NULL
        """)

    def save(self, ref: EvidenceRef) -> EvidenceRef:
        """Insert or update an evidence ref. Returns the saved ref."""
        created_at_str = (
            ref.created_at.isoformat() if isinstance(ref.created_at, datetime)
            else (ref.created_at or "")
        )
        expires_at_str = (
            ref.expires_at.isoformat() if isinstance(ref.expires_at, datetime)
            else (ref.expires_at if ref.expires_at else None)
        )
        self._conn.execute(
            f"""
            INSERT INTO {self._schema}.evidence_refs
                (evidence_id, project_id, strategy_lineage_id, strategy_version_id,
                 artifact_type, source_system, uri, sha256, schema_version,
                 created_at, producer, status, verification_status,
                 verification_error, expires_at, metadata)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16)
            ON CONFLICT (evidence_id) DO UPDATE SET
                verification_status = EXCLUDED.verification_status,
                verification_error = EXCLUDED.verification_error,
                uri = EXCLUDED.uri,
                sha256 = EXCLUDED.sha256
            """,
            [
                ref.evidence_id,
                ref.project_id,
                ref.strategy_lineage_id,
                ref.strategy_version_id,
                ref.artifact_type.value if isinstance(ref.artifact_type, ArtifactType) else ref.artifact_type,
                ref.source_system,
                ref.uri,
                ref.sha256,
                ref.schema_version,
                created_at_str,
                ref.producer,
                ref.status,
                ref.verification_status.value if isinstance(ref.verification_status, VerificationStatus) else ref.verification_status,
                ref.verification_error,
                expires_at_str,
                ref.metadata,
            ],
        )
        return ref

    def get(self, evidence_id: str, project_id: str) -> EvidenceRef | None:
        """Get an evidence ref by ID, scoped to project."""
        row = self._conn.execute(
            f"""
            SELECT evidence_id, project_id, strategy_lineage_id, strategy_version_id,
                   artifact_type, source_system, uri, sha256, schema_version,
                   created_at, producer, status, verification_status,
                   verification_error, expires_at, metadata
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
            SELECT evidence_id, project_id, strategy_lineage_id, strategy_version_id,
                   artifact_type, source_system, uri, sha256, schema_version,
                   created_at, producer, status, verification_status,
                   verification_error, expires_at, metadata
            FROM {self._schema}.evidence_refs
            WHERE project_id = $1
            ORDER BY created_at DESC
            """,
            [project_id],
        ).fetchall()
        return [self._row_to_ref(row) for row in rows]

    def list_by_strategy_lineage(
        self, project_id: str, strategy_lineage_id: str
    ) -> list[EvidenceRef]:
        """List all evidence refs for a strategy lineage within a project."""
        rows = self._conn.execute(
            f"""
            SELECT evidence_id, project_id, strategy_lineage_id, strategy_version_id,
                   artifact_type, source_system, uri, sha256, schema_version,
                   created_at, producer, status, verification_status,
                   verification_error, expires_at, metadata
            FROM {self._schema}.evidence_refs
            WHERE project_id = $1 AND strategy_lineage_id = $2
            ORDER BY created_at DESC
            """,
            [project_id, strategy_lineage_id],
        ).fetchall()
        return [self._row_to_ref(row) for row in rows]

    def update_verification(
        self,
        evidence_id: str,
        project_id: str,
        verification_status: VerificationStatus,
        error: str | None = None,
    ) -> EvidenceRef | None:
        """Update verification status. Returns updated ref or None if not found."""
        result = self._conn.execute(
            f"""
            UPDATE {self._schema}.evidence_refs
            SET verification_status = $1, verification_error = $2
            WHERE evidence_id = $3 AND project_id = $4
            """,
            [
                verification_status.value if isinstance(verification_status, VerificationStatus) else verification_status,
                error,
                evidence_id,
                project_id,
            ],
        )
        if result.rowcount == 0:
            return None
        return self.get(evidence_id, project_id)

    @staticmethod
    def _row_to_ref(row: tuple) -> EvidenceRef:
        """Convert a database row to an EvidenceRef model."""
        # Row layout: evidence_id(0), project_id(1), strategy_lineage_id(2),
        # strategy_version_id(3), artifact_type(4), source_system(5), uri(6),
        # sha256(7), schema_version(8), created_at(9), producer(10), status(11),
        # verification_status(12), verification_error(13), expires_at(14), metadata(15)
        created_at_val = row[9]
        if isinstance(created_at_val, str) and created_at_val:
            try:
                created_at_val = datetime.fromisoformat(created_at_val)
            except ValueError:
                created_at_val = None
        else:
            created_at_val = None

        expires_at_val = row[14]
        if isinstance(expires_at_val, str) and expires_at_val:
            try:
                expires_at_val = datetime.fromisoformat(expires_at_val)
            except ValueError:
                expires_at_val = None
        else:
            expires_at_val = None

        return EvidenceRef(
            evidence_id=row[0],
            project_id=row[1],
            strategy_lineage_id=row[2],
            strategy_version_id=row[3],
            artifact_type=row[4],
            source_system=row[5],
            uri=row[6],
            sha256=row[7],
            schema_version=row[8],
            created_at=created_at_val,
            producer=row[10],
            status=row[11],
            verification_status=row[12],
            verification_error=row[13],
            expires_at=expires_at_val,
            metadata=row[15] if isinstance(row[15], dict) else {},
        )
