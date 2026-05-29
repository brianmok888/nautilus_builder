"""Shared Postgres connection management for Nautilus Builder."""
from __future__ import annotations

import os
from typing import Any


def get_database_url(env_var: str = "BUILDER_DATABASE_URL") -> str | None:
    """Return the configured Postgres DSN, or None if not configured."""
    dsn = os.environ.get(env_var, "").strip()
    return dsn or None


def connect(dsn: str | None = None, *, env_var: str = "BUILDER_DATABASE_URL") -> Any:
    """Connect to Postgres using psycopg3. Raises if psycopg not installed or DSN missing."""
    import psycopg

    url = dsn or get_database_url(env_var)
    if not url:
        raise ValueError(f"Postgres DSN not configured. Set {env_var}.")
    return psycopg.connect(url, autocommit=True)


def ensure_schema(conn: Any, schema: str = "builder") -> None:
    """Create the builder schema if it doesn't exist."""
    conn.execute(f"CREATE SCHEMA IF NOT EXISTS {schema}")
