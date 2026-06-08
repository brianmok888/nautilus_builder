"""Postgres-backed Builder config repository.

Stores non-secret configuration in the builder_config table.
Does not store credentials, tokens, or secrets.
"""
from __future__ import annotations

import json
from typing import Any

from packages.postgres.identifiers import postgres_table, safe_postgres_identifier


class PostgresConfigRepository:
    """Key-value config store backed by Postgres builder_config table."""

    def __init__(self, conn: Any, schema: str = "builder") -> None:
        self._conn = conn
        self._schema = safe_postgres_identifier(schema)

    def _table(self, name: str) -> str:
        return postgres_table(self._schema, name)

    def get(self, key: str) -> dict[str, Any] | None:
        """Get a config value by key. Returns None if not found."""
        row = self._conn.execute(
            f"SELECT value FROM {self._table('builder_config')} WHERE key = %s",
            (key,),
        ).fetchone()
        if not row:
            return None
        value = row[0]
        if isinstance(value, str):
            return json.loads(value)
        return value

    def set(self, key: str, value: dict[str, Any], *, updated_by: str | None = None) -> None:
        """Set a config value. Upserts the row."""
        self._conn.execute(
            f"INSERT INTO {self._table('builder_config')} (key, value, updated_at, updated_by) "
            f"VALUES (%s, %s, now(), %s) "
            f"ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value, updated_at = now(), updated_by = EXCLUDED.updated_by",
            (key, json.dumps(value), updated_by),
        )

    def list_all(self) -> list[dict[str, Any]]:
        """List all config entries."""
        rows = self._conn.execute(
            f"SELECT key, value, updated_at, updated_by FROM {self._table('builder_config')} ORDER BY key"
        ).fetchall()
        return [
            {
                "key": r[0],
                "value": json.loads(r[1]) if isinstance(r[1], str) else r[1],
                "updated_at": r[2].isoformat().replace("+00:00", "Z") if hasattr(r[2], "isoformat") else str(r[2]),
                "updated_by": r[3],
            }
            for r in rows
        ]
