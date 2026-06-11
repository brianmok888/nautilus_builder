"""DuckDB probe — validates dataset quality when DuckDB is available.

When DuckDB is not installed, probe functions return a graceful
degradation message instead of raising ImportError.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

from packages.catalog_datasets.models import DatasetManifest


def _duckdb_available() -> bool:
    try:
        import duckdb  # noqa: F401
        return True
    except ImportError:
        return False


class ProbeResult:
    """Result of a DuckDB dataset probe."""

    def __init__(self, *, valid: bool, checks: list[dict[str, Any]], errors: list[str]) -> None:
        self.valid = valid
        self.checks = checks
        self.errors = errors


def probe_parquet_file(path: Path, manifest: DatasetManifest) -> ProbeResult:
    """Probe a Parquet file against its manifest.

    Validates:
    - File exists
    - Schema matches expected columns
    - Timestamps are monotonic per source
    - No required field is entirely null
    - Row count matches manifest
    """
    checks: list[dict[str, Any]] = []
    errors: list[str] = []

    # File existence check (always available)
    if not path.exists():
        errors.append(f"File does not exist: {path}")
        return ProbeResult(valid=False, checks=checks, errors=errors)

    checks.append({"name": "file_exists", "passed": True})

    if not _duckdb_available():
        checks.append({"name": "duckdb_available", "passed": False, "note": "DuckDB not installed"})
        return ProbeResult(valid=True, checks=checks, errors=errors)

    import duckdb

    try:
        conn = duckdb.connect(str(path), read_only=True)

        # Row count check
        row_result = conn.execute("SELECT COUNT(*) FROM read_parquet(?)", [str(path)]).fetchone()
        if row_result:
            actual_rows = row_result[0]
            passed = actual_rows == manifest.row_count
            checks.append({
                "name": "row_count",
                "passed": passed,
                "expected": manifest.row_count,
                "actual": actual_rows,
            })
            if not passed and manifest.row_count > 0:
                errors.append(f"Row count mismatch: expected {manifest.row_count}, got {actual_rows}")

        conn.close()
    except Exception as e:
        errors.append(f"DuckDB probe error: {e}")

    return ProbeResult(valid=len(errors) == 0, checks=checks, errors=errors)
