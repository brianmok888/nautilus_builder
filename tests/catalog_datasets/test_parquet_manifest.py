"""Parquet dataset manifest tests — Segment 6."""
import pytest

from packages.catalog_datasets.models import DatasetManifest, DatasetFormat
from packages.catalog_datasets.parquet_manifest import validate_manifest


class TestDatasetManifest:
    def test_manifest_fields(self) -> None:
        m = DatasetManifest(
            dataset_id="ds_001",
            venue="BINANCE",
            instrument_id="BTCUSDT-PERP.BINANCE",
            timeframe="1-MINUTE",
            start_ts="2024-01-01T00:00:00Z",
            end_ts="2024-06-01T00:00:00Z",
            row_count=100000,
            storage_uri="s3://data/ds_001.parquet",
            format=DatasetFormat.PARQUET,
            content_sha256="abc123",
        )
        assert m.dataset_id == "ds_001"
        assert m.format == DatasetFormat.PARQUET

    def test_manifest_requires_dataset_id(self) -> None:
        with pytest.raises(Exception):
            DatasetManifest(
                venue="BINANCE",
                instrument_id="BTCUSDT-PERP.BINANCE",
                timeframe="1-MINUTE",
                start_ts="2024-01-01",
                end_ts="2024-06-01",
                row_count=100,
                storage_uri="s3://data/ds.parquet",
                format=DatasetFormat.PARQUET,
                content_sha256="abc",
            )


class TestManifestValidation:
    def test_valid_manifest_passes(self) -> None:
        m = DatasetManifest(
            dataset_id="ds_001",
            venue="BINANCE",
            instrument_id="BTCUSDT-PERP.BINANCE",
            timeframe="1-MINUTE",
            start_ts="2024-01-01T00:00:00Z",
            end_ts="2024-06-01T00:00:00Z",
            row_count=100000,
            storage_uri="s3://data/ds_001.parquet",
            format=DatasetFormat.PARQUET,
            content_sha256="a" * 64,
        )
        errors = validate_manifest(m)
        assert errors == []

    def test_manifest_with_short_hash_warns(self) -> None:
        m = DatasetManifest(
            dataset_id="ds_001",
            venue="BINANCE",
            instrument_id="BTCUSDT-PERP.BINANCE",
            timeframe="1-MINUTE",
            start_ts="2024-01-01",
            end_ts="2024-06-01",
            row_count=100,
            storage_uri="local",
            format=DatasetFormat.PARQUET,
            content_sha256="short",
        )
        errors = validate_manifest(m)
        assert any("sha256" in e.lower() for e in errors)

    def test_manifest_with_zero_rows_warns(self) -> None:
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
        errors = validate_manifest(m)
        assert any("row" in e.lower() for e in errors)
