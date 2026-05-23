from __future__ import annotations

import os
from typing import Any


def connect_builder_postgres(dsn_env: str = "BUILDER_DATABASE_URL") -> Any:
    dsn = os.getenv(dsn_env)
    if not dsn:
        raise ValueError(f"Postgres DSN environment variable is not configured: {dsn_env}")

    try:
        import psycopg
    except ImportError as exc:
        raise RuntimeError("psycopg is required for real Builder Postgres connections") from exc

    return psycopg.connect(dsn)
