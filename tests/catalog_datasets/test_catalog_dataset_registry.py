from __future__ import annotations

from pathlib import Path

import pytest

from packages.auth import ProjectScopeError, UserProjectContext
from packages.catalog_datasets import CatalogDataset, CatalogDatasetRegistryService


def _dataset(tmp_path: Path, *, catalog_path: Path | None = None) -> CatalogDataset:
    return CatalogDataset(
        dataset_id="ds_btcusdt_perp_2024_q1",
        user_id="user_123",
        project_id="project_alpha",
        adapter_id="BINANCE_PERP",
        instrument_id="BTCUSDT-PERP",
        data_type="quote_ticks",
        timeframe="1m",
        market_type="crypto_perp",
        date_range="2024-01-01:2024-03-01",
        catalog_path=(catalog_path or (tmp_path / "catalog")).as_posix(),
    )


def test_selects_user_catalog_dataset_with_full_backtest_profile_match(tmp_path) -> None:
    context = UserProjectContext(user_id="user_123", project_id="project_alpha")
    service = CatalogDatasetRegistryService()
    dataset = service.register_dataset(_dataset(tmp_path))

    selected = service.select_dataset(
        context=context,
        dataset_id=dataset.dataset_id,
        adapter_id="BINANCE_PERP",
        instrument_id="BTCUSDT-PERP",
        data_type="quote_ticks",
        timeframe="1m",
        market_type="crypto_perp",
        date_range="2024-01-01:2024-03-01",
    )

    assert selected.dataset_id == "ds_btcusdt_perp_2024_q1"
    assert selected.catalog_path.endswith("catalog")
    assert selected.scoped_artifact.artifact_type == "CatalogDataset"


def test_rejects_catalog_dataset_profile_mismatch(tmp_path) -> None:
    context = UserProjectContext(user_id="user_123", project_id="project_alpha")
    service = CatalogDatasetRegistryService()
    dataset = service.register_dataset(_dataset(tmp_path))

    with pytest.raises(ValueError, match="dataset field mismatch: instrument_id expected ETHUSDT-PERP, got BTCUSDT-PERP"):
        service.select_dataset(
            context=context,
            dataset_id=dataset.dataset_id,
            adapter_id="BINANCE_PERP",
            instrument_id="ETHUSDT-PERP",
            data_type="quote_ticks",
            timeframe="1m",
            market_type="crypto_perp",
            date_range="2024-01-01:2024-03-01",
        )


def test_rejects_cross_project_catalog_dataset_selection(tmp_path) -> None:
    service = CatalogDatasetRegistryService()
    dataset = service.register_dataset(_dataset(tmp_path))
    intruder = UserProjectContext(user_id="user_123", project_id="project_beta")

    with pytest.raises(ProjectScopeError, match="outside user/project scope"):
        service.select_dataset(
            context=intruder,
            dataset_id=dataset.dataset_id,
            adapter_id="BINANCE_PERP",
            instrument_id="BTCUSDT-PERP",
            data_type="quote_ticks",
            timeframe="1m",
            market_type="crypto_perp",
            date_range="2024-01-01:2024-03-01",
        )


def test_rejects_catalog_path_outside_configured_root(tmp_path) -> None:
    catalog_root = tmp_path / "catalog_root"
    outside = tmp_path / "outside" / "catalog"
    service = CatalogDatasetRegistryService(catalog_root=catalog_root)

    with pytest.raises(ValueError, match="catalog path outside configured root"):
        service.register_dataset(_dataset(tmp_path, catalog_path=outside))


def test_rejects_catalog_path_traversing_symlinked_directory(tmp_path) -> None:
    catalog_root = tmp_path / "catalog_root"
    catalog_root.mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()
    symlinked = catalog_root / "linked"
    symlinked.symlink_to(outside, target_is_directory=True)

    service = CatalogDatasetRegistryService(catalog_root=catalog_root)

    with pytest.raises(ValueError, match="catalog path must not traverse symlinks"):
        service.register_dataset(_dataset(tmp_path, catalog_path=symlinked / "catalog"))
