"""Schema DDL for Nautilus Builder Postgres tables."""
from __future__ import annotations

from typing import Any

SCHEMA_VERSION = 1

BUILDER_SCHEMA_SQL = """
-- Strategies: one row per strategy, stores latest status and spec
CREATE TABLE IF NOT EXISTS {schema}.strategies (
    strategy_id       TEXT PRIMARY KEY,
    strategy_lineage_id TEXT NOT NULL,
    status            TEXT NOT NULL DEFAULT 'draft',
    latest_spec       JSONB NOT NULL DEFAULT '{{}}',
    created_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at        TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Strategy versions: full version history
CREATE TABLE IF NOT EXISTS {schema}.strategy_versions (
    strategy_version_id TEXT PRIMARY KEY,
    strategy_id         TEXT NOT NULL REFERENCES {schema}.strategies(strategy_id) ON DELETE CASCADE,
    strategy_lineage_id TEXT NOT NULL,
    spec                JSONB NOT NULL,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Adapter registry: adapter profiles for dropdowns
CREATE TABLE IF NOT EXISTS {schema}.adapters (
    adapter_id  TEXT PRIMARY KEY,
    enabled     BOOLEAN NOT NULL DEFAULT true,
    venue       TEXT NOT NULL,
    asset_class TEXT NOT NULL,
    data_modes  JSONB NOT NULL DEFAULT '[]',
    execution_modes JSONB NOT NULL DEFAULT '{{}}'
);

-- Instrument registry: instruments per adapter for dropdowns
CREATE TABLE IF NOT EXISTS {schema}.instruments (
    adapter_id          TEXT NOT NULL REFERENCES {schema}.adapters(adapter_id) ON DELETE CASCADE,
    instrument_id       TEXT NOT NULL,
    market_type         TEXT NOT NULL,
    supported_data_types JSONB NOT NULL DEFAULT '[]',
    supported_timeframes JSONB NOT NULL DEFAULT '[]',
    available_date_ranges JSONB NOT NULL DEFAULT '[]',
    PRIMARY KEY (adapter_id, instrument_id)
);

-- Schema version tracking
CREATE TABLE IF NOT EXISTS {schema}.schema_version (
    version INT PRIMARY KEY,
    applied_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
"""


def apply_migrations(conn: Any, schema: str = "builder") -> None:
    """Apply all builder schema migrations. Idempotent."""
    conn.execute(f"CREATE SCHEMA IF NOT EXISTS {schema}")
    conn.execute(BUILDER_SCHEMA_SQL.format(schema=schema))
    conn.execute(
        f"INSERT INTO {schema}.schema_version (version) VALUES (%s) ON CONFLICT DO NOTHING",
        (SCHEMA_VERSION,),
    )
