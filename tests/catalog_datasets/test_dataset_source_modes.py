from __future__ import annotations

from pathlib import Path

import pytest

from packages.catalog_datasets import CatalogDataset, CatalogDatasetRegistryService


def _base_dataset(tmp_path: Path, **overrides: object) -> CatalogDataset:
    payload: dict[str, object] = {
        "dataset_id": "ds_btcusdt_perp_2025",
        "user_id": "user_123",
        "project_id": "project_alpha",
        "adapter_id": "BINANCE_PERP",
        "instrument_id": "BTCUSDT-PERP",
        "data_type": "quote_ticks",
        "timeframe": "1m",
        "market_type": "crypto_perp",
        "date_range": "2025-01-01:2025-03-01",
        "catalog_path": (tmp_path / "catalogs" / "ds_btcusdt_perp_2025").as_posix(),
    }
    payload.update(overrides)
    return CatalogDataset.model_validate(payload)


def test_catalog_dataset_defaults_to_read_only_catalog_source_mode(tmp_path) -> None:
    dataset = _base_dataset(tmp_path)

    assert dataset.source_mode == "catalog"
    assert dataset.cache_mode == "read_only"
    assert dataset.manifest_ref is None
    assert dataset.cache_key == "ds_btcusdt_perp_2025"


def test_external_mirror_source_requires_builder_manifest_ref(tmp_path) -> None:
    with pytest.raises(ValueError, match="manifest_ref is required"):
        _base_dataset(tmp_path, source_mode="external_mirror_manifest", cache_mode="refreshable_manifest")

    with pytest.raises(ValueError, match="manifest_ref must be a Builder artifact"):
        _base_dataset(
            tmp_path,
            source_mode="external_mirror_manifest",
            cache_mode="refreshable_manifest",
            manifest_ref="https://example.com/manifest.json",
        )

    dataset = _base_dataset(
        tmp_path,
        source_mode="external_mirror_manifest",
        cache_mode="refreshable_manifest",
        manifest_ref="artifact://builder/project_alpha/user_123/DatasetManifest/ds_btcusdt_perp_2025",
    )

    assert dataset.source_mode == "external_mirror_manifest"
    assert dataset.cache_mode == "refreshable_manifest"


def test_fixture_source_modes_are_explicitly_fixture_cache_only(tmp_path) -> None:
    with pytest.raises(ValueError, match="fixture source modes require fixture cache mode"):
        _base_dataset(tmp_path, source_mode="local_fixture", cache_mode="read_only")

    dataset = _base_dataset(tmp_path, source_mode="local_fixture", cache_mode="fixture")

    assert dataset.source_mode == "local_fixture"
    assert dataset.cache_mode == "fixture"


def test_dataset_cache_key_rejects_unsafe_identifiers(tmp_path) -> None:
    with pytest.raises(ValueError, match="cache_key must be a safe identifier"):
        _base_dataset(tmp_path, cache_key="../secret")


def test_registry_preserves_dataset_source_policy_when_registering(tmp_path) -> None:
    service = CatalogDatasetRegistryService(catalog_root=tmp_path)
    dataset = _base_dataset(
        tmp_path,
        source_mode="user_fetched_manifest",
        cache_mode="refreshable_manifest",
        manifest_ref="artifact://builder/project_alpha/user_123/DatasetManifest/ds_btcusdt_perp_2025",
    )

    registered = service.register_dataset(dataset)

    assert registered.source_mode == "user_fetched_manifest"
    assert registered.cache_mode == "refreshable_manifest"
    assert registered.manifest_ref == "artifact://builder/project_alpha/user_123/DatasetManifest/ds_btcusdt_perp_2025"
