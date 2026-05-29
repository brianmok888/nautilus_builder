"""Shared Postgres connection management for Nautilus Builder.

Provides a unified interface over both raw psycopg3 connections and
psycopg_pool connection pools. Both support .execute() and .transaction().
"""
from __future__ import annotations

import os
from contextlib import contextmanager
from typing import Any, Generator


def get_database_url(env_var: str = "BUILDER_DATABASE_URL") -> str | None:
    """Return the configured Postgres DSN, or None if not configured."""
    dsn = os.environ.get(env_var, "").strip()
    return dsn or None


def connect(dsn: str | None = None, *, env_var: str = "BUILDER_DATABASE_URL") -> Any:
    """Connect to Postgres using psycopg3. Single autocommit connection."""
    import psycopg

    url = dsn or get_database_url(env_var)
    if not url:
        raise ValueError(f"Postgres DSN not configured. Set {env_var}.")
    return psycopg.connect(url, autocommit=True)


class PooledConnection:
    """Wraps a psycopg_pool.ConnectionPool.

    Provides .execute() and .transaction() with the same interface as a
    raw psycopg3 autocommit connection, but checks out connections from
    the pool behind the scenes.
    """

    def __init__(self, pool: Any) -> None:
        self._pool = pool

    def execute(self, query: str, params: tuple | None = None) -> Any:
        """Execute a single statement on a checked-out connection."""
        with self._pool.connection() as conn:
            return conn.execute(query, params)

    @contextmanager
    def transaction(self) -> Generator[Any, None, None]:
        """Context manager yielding a connection with an atomic transaction.

        Usage (same as psycopg3):
            with conn.transaction():
                conn.execute(...)
                conn.execute(...)
        """
        with self._pool.connection() as conn:
            with conn.transaction():
                yield conn

    @property
    def pool(self) -> Any:
        return self._pool

    def close(self) -> None:
        self._pool.close()


def connect_pool(dsn: str | None = None, *, env_var: str = "BUILDER_DATABASE_URL", min_size: int = 2, max_size: int = 10) -> PooledConnection | Any:
    """Create a pooled or single Postgres connection.

    Returns a PooledConnection when psycopg_pool is available,
    otherwise falls back to a single autocommit psycopg3 connection.
    Both support .execute() and .transaction() with the same interface.
    """
    import psycopg

    url = dsn or get_database_url(env_var)
    if not url:
        raise ValueError(f"Postgres DSN not configured. Set {env_var}.")

    try:
        from psycopg_pool import ConnectionPool
        pool = ConnectionPool(
            url,
            min_size=min_size,
            max_size=max_size,
            open=False,
        )
        pool.open()
        return PooledConnection(pool)
    except ImportError:
        return psycopg.connect(url, autocommit=True)
