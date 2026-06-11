"""DuckDB probe tests — Segment 6."""
from pathlib import Path

from packages.catalog_datasets.duckdb_probe import probe_parquet_file, _duckdb_available
from packages.catalog_datasets.models import DatasetManifest, DatasetFormat


class TestDuckDBProbe:
    def test_probe_missing_file(self) -> None:
        m = DatasetManifest(
            dataset_id="ds_missing",
            venue="BINANCE",
            instrument_id="BTCUSDT-PERP.BINANCE",
            timeframe="1-MINUTE",
            start_ts="2024-01-01",
            end_ts="2024-06-01",
            row_count=100,
            storage_uri="local",
            format=DatasetFormat.PARQUET,
            content_sha256="a" * 64,
        )
        result = probe_parquet_file(Path("/nonexistent/file.parquet"), m)
        assert not result.valid
        assert any("does not exist" in e for e in result.errors)

    def test_probe_checks_file_existence(self) -> None:
        m = DatasetManifest(
            dataset_id="ds_001",
            venue="BINANCE",
            instrument_id="BTCUSDT-PERP.BINANCE",
            timeframe="1-MINUTE",
            start_ts="2024-01-01",
            end_ts="2024-06-01",
            row_count=0,
            storage_uri="local",
            format=DatasetFormat.PARQUET,
            content_sha256="a" * 64,
        )
        result = probe_parquet_file(Path("/nonexistent.parquet"), m)
        assert any(c["name"] == "file_exists" for c in result.checks) or len(result.errors) > 0

    def test_duckdb_available_returns_bool(self) -> None:
        # Just verify it doesn't crash
        result = _duckdb_available()
        assert isinstance(result, bool)
