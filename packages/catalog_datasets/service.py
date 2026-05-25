from __future__ import annotations

from pathlib import Path

from packages.auth import UserProjectContext, assert_same_project

from .models import CatalogDataset


class CatalogPathPolicy:
    """Allowlist Nautilus catalog paths under one configured root."""

    def __init__(self, root: str | Path) -> None:
        self.root = Path(root).expanduser().resolve(strict=False)

    def validate_path(self, catalog_path: str | Path) -> Path:
        path = Path(catalog_path).expanduser()
        candidate = path if path.is_absolute() else self.root / path
        if self._contains_symlink(candidate):
            raise ValueError("catalog path must not traverse symlinks")
        resolved = candidate.resolve(strict=False)
        if not resolved.is_relative_to(self.root):
            raise ValueError("catalog path outside configured root")
        return resolved

    @staticmethod
    def _contains_symlink(path: Path) -> bool:
        probe = Path(path.anchor) if path.is_absolute() else Path()
        parts = path.parts[1:] if path.is_absolute() else path.parts
        for part in parts:
            probe = probe / part
            if probe.is_symlink():
                return True
        return False


class CatalogDatasetRegistryService:
    """Project-scoped registry for user-selected Nautilus catalog datasets."""

    def __init__(self, datasets: list[CatalogDataset] | None = None, *, catalog_root: str | Path | None = None) -> None:
        self._datasets: dict[str, CatalogDataset] = {}
        self._path_policy = CatalogPathPolicy(catalog_root) if catalog_root is not None else None
        for dataset in datasets or []:
            self.register_dataset(dataset)

    def register_dataset(self, dataset: CatalogDataset) -> CatalogDataset:
        registered = self._normalize_dataset_path(dataset)
        self._datasets[registered.dataset_id] = registered
        return registered

    def get_dataset(self, dataset_id: str) -> CatalogDataset:
        try:
            return self._datasets[dataset_id]
        except KeyError as exc:
            raise ValueError(f"unknown catalog dataset: {dataset_id}") from exc

    def list_datasets(self, *, context: UserProjectContext) -> list[CatalogDataset]:
        return [
            dataset
            for dataset in self._datasets.values()
            if dataset.user_id == context.user_id and dataset.project_id == context.project_id
        ]

    def select_dataset(
        self,
        *,
        context: UserProjectContext,
        dataset_id: str,
        adapter_id: str,
        instrument_id: str,
        data_type: str,
        timeframe: str,
        market_type: str,
        date_range: str,
    ) -> CatalogDataset:
        dataset = self.get_dataset(dataset_id)
        assert_same_project(context, dataset.scoped_artifact)
        expected = {
            "adapter_id": adapter_id,
            "instrument_id": instrument_id,
            "data_type": data_type,
            "timeframe": timeframe,
            "market_type": market_type,
            "date_range": date_range,
        }
        for field_name, expected_value in expected.items():
            actual_value = getattr(dataset, field_name)
            if actual_value != expected_value:
                raise ValueError(
                    f"dataset field mismatch: {field_name} expected {expected_value}, got {actual_value}"
                )
        return self._normalize_dataset_path(dataset)

    def _normalize_dataset_path(self, dataset: CatalogDataset) -> CatalogDataset:
        if self._path_policy is None:
            return dataset
        resolved = self._path_policy.validate_path(dataset.catalog_path)
        return dataset.model_copy(update={"catalog_path": resolved.as_posix()})
