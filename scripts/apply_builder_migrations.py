#!/usr/bin/env python3
"""Apply pending Builder schema migrations to the Postgres database.

Reads BUILDER_DATABASE_URL from the environment, connects, and runs
any migrations not yet recorded in builder.schema_migrations.

This script is safe to run repeatedly — it only applies pending migrations.

Usage:
    export BUILDER_DATABASE_URL="postgresql://builder:builder_dev@localhost:5432/nautilus_builder"
    uv run python scripts/apply_builder_migrations.py
"""
from __future__ import annotations

import os
import sys


def main() -> int:
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)

    from packages.postgres.connection import connect
    from packages.postgres.migrations import apply_migrations

    dsn = os.environ.get("BUILDER_DATABASE_URL", "").strip()
    if not dsn:
        print("Error: BUILDER_DATABASE_URL is not set.", file=sys.stderr)
        print("Example: export BUILDER_DATABASE_URL=\"postgresql://builder:builder_dev@localhost:5432/nautilus_builder\"", file=sys.stderr)
        return 1

    conn = connect(dsn)
    try:
        applied = apply_migrations(conn, schema="builder")
        if applied:
            print(f"Applied {len(applied)} migration(s):")
            for name in applied:
                print(f"  {name}")
        else:
            print("No pending migrations. Schema is up to date.")
    finally:
        conn.close()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
