"""Versioned Postgres schema migrations for Nautilus Builder.

Each migration has an `up` and optional `down` SQL statement.
`apply_migrations` runs only pending migrations in order.
`rollback` rolls back the last applied migration.
"""
from __future__ import annotations

from typing import Any, NamedTuple


class Migration(NamedTuple):
    version: int
    name: str
    up: str
    down: str


MIGRATIONS: list[Migration] = [
    Migration(
        version=1,
        name="initial_schema",
        up="""
        CREATE TABLE IF NOT EXISTS {schema}.strategies (
            strategy_id       TEXT PRIMARY KEY,
            strategy_lineage_id TEXT NOT NULL,
            status            TEXT NOT NULL DEFAULT 'draft',
            latest_spec       JSONB NOT NULL DEFAULT '{{}}',
            created_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at        TIMESTAMPTZ NOT NULL DEFAULT now()
        );

        CREATE TABLE IF NOT EXISTS {schema}.strategy_versions (
            strategy_version_id TEXT PRIMARY KEY,
            strategy_id         TEXT NOT NULL REFERENCES {schema}.strategies(strategy_id) ON DELETE CASCADE,
            strategy_lineage_id TEXT NOT NULL,
            spec                JSONB NOT NULL,
            created_at          TIMESTAMPTZ NOT NULL DEFAULT now()
        );

        CREATE TABLE IF NOT EXISTS {schema}.adapters (
            adapter_id  TEXT PRIMARY KEY,
            enabled     BOOLEAN NOT NULL DEFAULT true,
            venue       TEXT NOT NULL,
            asset_class TEXT NOT NULL,
            data_modes  JSONB NOT NULL DEFAULT '[]',
            execution_modes JSONB NOT NULL DEFAULT '{{}}'
        );

        CREATE TABLE IF NOT EXISTS {schema}.instruments (
            adapter_id          TEXT NOT NULL REFERENCES {schema}.adapters(adapter_id) ON DELETE CASCADE,
            instrument_id       TEXT NOT NULL,
            market_type         TEXT NOT NULL,
            supported_data_types JSONB NOT NULL DEFAULT '[]',
            supported_timeframes JSONB NOT NULL DEFAULT '[]',
            available_date_ranges JSONB NOT NULL DEFAULT '[]',
            PRIMARY KEY (adapter_id, instrument_id)
        );

        CREATE TABLE IF NOT EXISTS {schema}.schema_migrations (
            version     INT PRIMARY KEY,
            name        TEXT NOT NULL,
            applied_at  TIMESTAMPTZ NOT NULL DEFAULT now()
        );
        """,
        down="""
        DELETE FROM {schema}.schema_migrations WHERE version = 1;
        DROP TABLE IF EXISTS {schema}.schema_migrations;
        DROP TABLE IF EXISTS {schema}.instruments;
        DROP TABLE IF EXISTS {schema}.adapters;
        DROP TABLE IF EXISTS {schema}.strategy_versions;
        DROP TABLE IF EXISTS {schema}.strategies;
        """,
    ),
]


def ensure_schema(conn: Any, schema: str = "builder") -> None:
    """Create the builder schema and schema_migrations table if they don't exist."""
    conn.execute(f"CREATE SCHEMA IF NOT EXISTS {schema}")


def current_version(conn: Any, schema: str = "builder") -> int:
    """Return the highest applied migration version, or 0 if none."""
    try:
        row = conn.execute(
            f"SELECT MAX(version) FROM {schema}.schema_migrations"
        ).fetchone()
        return row[0] if row and row[0] is not None else 0
    except Exception:
        return 0


def apply_migrations(conn: Any, schema: str = "builder") -> list[str]:
    """Run all pending migrations. Returns list of applied migration names."""
    ensure_schema(conn, schema)
    applied: list[str] = []
    version = current_version(conn, schema)
    for migration in MIGRATIONS:
        if migration.version > version:
            conn.execute(migration.up.format(schema=schema))
            conn.execute(
                f"INSERT INTO {schema}.schema_migrations (version, name) VALUES (%s, %s) ON CONFLICT DO NOTHING",
                (migration.version, migration.name),
            )
            applied.append(f"v{migration.version}: {migration.name}")
    return applied


def rollback(conn: Any, schema: str = "builder", steps: int = 1) -> list[str]:
    """Roll back the last N migrations. Returns list of rolled-back names."""
    ensure_schema(conn, schema)
    rolled_back: list[str] = []
    version = current_version(conn, schema)
    for migration in reversed(MIGRATIONS):
        if len(rolled_back) >= steps:
            break
        if migration.version <= version and migration.down:
            conn.execute(migration.down.format(schema=schema))
            rolled_back.append(f"v{migration.version}: {migration.name}")
    return rolled_back
