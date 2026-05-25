from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

from packages.auth import UserProjectContext
from packages.catalog_datasets import CatalogDataset
from packages.backtest_runner import (
    STRATEGY_SPEC_CATALOG_REPLAY_MODE,
    STRATEGY_SPEC_SYNTHETIC_CATALOG_SMOKE_MODE,
    run_strategy_spec_catalog_replay,
    run_strategy_spec_synthetic_catalog_smoke,
)
from tests.strategy_spec.test_schema_valid import make_valid_spec


def _dataset(tmp_path: Path, context: UserProjectContext, spec: dict[str, object]) -> CatalogDataset:
    return CatalogDataset(
        dataset_id="ds_btcusdt_perp_2025",
        user_id=context.user_id,
        project_id=context.project_id,
        adapter_id=str(spec["adapter_id"]),
        instrument_id=str(spec["instrument_id"]),
        data_type="quote_ticks",
        timeframe="1m",
        market_type="crypto_perp",
        date_range=f"{spec['data_range']['start']}:{spec['data_range']['end']}",
        catalog_path=(tmp_path / "catalogs" / "ds_btcusdt_perp_2025").as_posix(),
        source="user_catalog",
    )


def _file_manifest(path: Path) -> dict[str, str]:
    return {
        file.relative_to(path).as_posix(): hashlib.sha256(file.read_bytes()).hexdigest()
        for file in sorted(path.rglob("*"))
        if file.is_file()
    }


def test_strategy_spec_user_catalog_replay_requires_configured_catalog_root(tmp_path) -> None:
    spec = make_valid_spec()
    context = UserProjectContext(user_id="user_123", project_id="project_alpha")
    dataset = _dataset(tmp_path, context, spec)

    with pytest.raises(ValueError, match="catalog_root is required"):
        run_strategy_spec_catalog_replay(strategy_spec_payload=spec, dataset=dataset, context=context)


def test_strategy_spec_user_catalog_replay_rejects_empty_existing_catalog(tmp_path) -> None:
    spec = make_valid_spec()
    context = UserProjectContext(user_id="user_123", project_id="project_alpha")
    dataset = _dataset(tmp_path, context, spec)
    Path(dataset.catalog_path).mkdir(parents=True)

    with pytest.raises(ValueError, match="user catalog has no matching quote_ticks"):
        run_strategy_spec_catalog_replay(
            strategy_spec_payload=spec,
            dataset=dataset,
            context=context,
            catalog_root=tmp_path,
        )


def test_strategy_spec_generated_catalog_replay_reads_user_catalog_without_synthetic_writes(tmp_path, monkeypatch) -> None:
    spec = make_valid_spec()
    context = UserProjectContext(user_id="user_123", project_id="project_alpha")
    dataset = _dataset(tmp_path, context, spec)

    smoke = run_strategy_spec_synthetic_catalog_smoke(
        strategy_spec_payload=spec,
        dataset=dataset,
        context=context,
        catalog_root=tmp_path,
    )
    catalog_path = Path(dataset.catalog_path)
    before_manifest = _file_manifest(catalog_path)

    from nautilus_trader.test_kit.stubs.data import TestDataStubs

    def fail_if_synthetic_tick_is_written(*args, **kwargs):  # noqa: ANN002, ANN003
        raise AssertionError("user-catalog replay must not synthesize TestDataStubs quote ticks")

    monkeypatch.setattr(TestDataStubs, "quote_tick", fail_if_synthetic_tick_is_written)

    evidence = run_strategy_spec_catalog_replay(
        strategy_spec_payload=spec,
        dataset=dataset,
        context=context,
        catalog_root=tmp_path,
    )

    assert smoke["engine_mode"] == STRATEGY_SPEC_SYNTHETIC_CATALOG_SMOKE_MODE
    assert smoke["dataset_source"] == "synthetic_test_kit"
    assert evidence["engine_mode"] == STRATEGY_SPEC_CATALOG_REPLAY_MODE
    assert evidence["dataset_source"] == "user_catalog"
    assert evidence["catalog_backed"] is True
    assert evidence["spec_generated"] is True
    assert evidence["strategy_path"] == "packages.nautilus_rule_graph.strategy:RuleGraphBacktestStrategy"
    assert evidence["strategy_spec_version"] == "0.1.0-draft.1"
    assert evidence["compile_hash"]
    assert evidence["dataset_id"] == "ds_btcusdt_perp_2025"
    assert evidence["catalog_data_count"] == smoke["catalog_data_count"]
    assert evidence["catalog_manifest_checksum"] == smoke["catalog_manifest_checksum"]
    assert evidence["catalog_manifest_file_count"] > 0
    assert evidence["iterations"] >= 5
    assert evidence["orders"] == 0
    assert evidence["positions"] == 0
    assert evidence["live_trading_enabled"] is False
    assert evidence["execution_authority"] is False
    assert evidence["credentials_used"] is False
    assert _file_manifest(catalog_path) == before_manifest
