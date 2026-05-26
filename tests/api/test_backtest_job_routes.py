from __future__ import annotations

from services.api.app import create_app


def test_backtest_job_can_be_created_read_and_cancelled() -> None:
    app = create_app()
    payload = {
        "strategy_version_id": "strategy_001_v001",
        "strategy_lineage_id": "lineage_strategy_001",
        "adapter_profile_id": "profile_001",
        "instrument_id": "BTCUSDT-PERP",
        "validation_report_id": "validation_001",
        "compile_hash": "a" * 64,
        "compile_artifact_id": "compile_001",
        "created_by": "operator_001",
        "data_range": "2024-01-01:2024-03-01",
    }

    created = app.post("/api/backtest-jobs", json=payload)
    job_id = created.json()["job_id"]
    detail = app.get(f"/api/backtest-jobs/{job_id}")
    cancelled = app.post(f"/api/backtest-jobs/{job_id}/cancel", json={})

    assert created.status_code == 201
    assert job_id == created.json()["backend_job_id"]
    assert detail.json()["status"] == "queued"
    assert detail.json()["created_by"] == "operator_001"
    assert detail.json()["strategy_spec_version_id"] == "strategy_001_v001"
    assert detail.json()["adapter_profile_id"] == "profile_001"
    assert detail.json()["data_range"] == "2024-01-01:2024-03-01"
    assert detail.json()["worker_id"] == "unassigned"
    assert detail.json()["result_artifact_refs"] == {}
    assert detail.json()["event_stream_id"] == f"builder:runtime:{job_id}"
    assert cancelled.json()["status"] == "cancel_requested"
    assert app.get(f"/api/backtest-jobs/{job_id}").json()["status"] == "cancel_requested"


def test_backtest_job_unknown_ids_return_404_instead_of_static_payloads() -> None:
    app = create_app()

    detail = app.get("/api/backtest-jobs/missing-job")
    cancelled = app.post("/api/backtest-jobs/missing-job/cancel", json={})

    assert detail.status_code == 404
    assert detail.json()["error"] == "backtest_job_not_found"
    assert cancelled.status_code == 404
    assert cancelled.json()["error"] == "backtest_job_not_found"


def test_backtest_job_events_are_observable_without_nd_stream_ownership() -> None:
    app = create_app()
    response = app.get("/api/backtest-jobs/bt_job_001/events")

    assert response.status_code == 200
    assert response.json()["stream_name"] == "builder:runtime:bt_job_001"
    assert response.json()["mode"] == "observational"
    assert response.json()["status"] == "observing"
    assert response.json()["events"] == []


def test_backtest_job_routes_enforce_user_project_scope_when_supplied() -> None:
    app = create_app()
    created = app.post(
        "/api/backtest-jobs",
        json={
            "strategy_version_id": "strategy_001_v001",
            "adapter_profile_id": "BINANCE_PERP",
            "instrument_id": "BTCUSDT-PERP",
            "validation_report_id": "validation_001",
            "compile_artifact_id": "compile_001",
            "created_by": "operator_001",
            "user_id": "user_123",
            "project_id": "project_alpha",
            "dataset_id": "ds_btcusdt_perp_2025",
            "catalog_path": "/tmp/nb/catalog",
        },
    )
    job_id = created.json()["job_id"]

    same_scope = app.get(f"/api/backtest-jobs/{job_id}?user_id=user_123&project_id=project_alpha")
    cross_scope = app.get(f"/api/backtest-jobs/{job_id}?user_id=user_123&project_id=project_beta")
    cancel_cross_scope = app.post(
        f"/api/backtest-jobs/{job_id}/cancel?user_id=user_123&project_id=project_beta",
        json={},
    )

    assert same_scope.status_code == 200
    assert same_scope.json()["user_id"] == "user_123"
    assert same_scope.json()["project_id"] == "project_alpha"
    assert same_scope.json()["dataset_id"] == "ds_btcusdt_perp_2025"
    assert cross_scope.status_code == 403
    assert cross_scope.json()["error"] == "forbidden"
    assert cancel_cross_scope.status_code == 403
    assert cancel_cross_scope.json()["error"] == "forbidden"

from packages.auth import UserProjectContext
from packages.backtest_jobs.service import BacktestJobService
from packages.catalog_datasets import CatalogDataset, CatalogDatasetRegistryService
from services.api.routes.backtest_jobs import backtest_job_payload, cancel_backtest_job_payload, create_backtest_job_payload


def _strict_context() -> UserProjectContext:
    return UserProjectContext(user_id="user_123", project_id="project_alpha")


def _strict_dataset_registry(tmp_path, context: UserProjectContext) -> CatalogDatasetRegistryService:
    registry = CatalogDatasetRegistryService(catalog_root=tmp_path)
    registry.register_dataset(
        CatalogDataset(
            dataset_id="ds_btcusdt_perp_2024_q1",
            user_id=context.user_id,
            project_id=context.project_id,
            adapter_id="BINANCE_PERP",
            instrument_id="BTCUSDT-PERP",
            data_type="quote_ticks",
            timeframe="1m",
            market_type="crypto_perp",
            date_range="2024-01-01:2024-03-01",
            catalog_path=(tmp_path / "catalogs" / "ds_btcusdt_perp_2024_q1").as_posix(),
        )
    )
    return registry


def _strict_payload() -> dict[str, object]:
    return {
        "strategy_version_id": "strategy_001_v001",
        "adapter_profile_id": "BINANCE_PERP",
        "instrument_id": "BTCUSDT-PERP",
        "validation_report_id": "validation_001",
        "compile_hash": "a" * 64,
        "compile_artifact_id": "compile_001",
        "created_by": "operator_001",
        "data_range": "2024-01-01:2024-03-01",
        "data_type": "quote_ticks",
        "timeframe": "1m",
        "market_type": "crypto_perp",
        "dataset_id": "ds_btcusdt_perp_2024_q1",
    }


def test_strict_backtest_job_creation_derives_scope_from_auth_context_and_ignores_spoofed_payload(tmp_path) -> None:
    context = _strict_context()
    service = BacktestJobService()
    registry = _strict_dataset_registry(tmp_path, context)
    payload = {
        **_strict_payload(),
        "user_id": "attacker",
        "project_id": "evil_project",
        "catalog_path": "/tmp/evil/catalog",
    }

    response = create_backtest_job_payload(
        service,
        payload,
        context=context,
        dataset_registry=registry,
        strict_scope=True,
    )

    body = response.json()
    assert response.status_code == 201
    assert body["user_id"] == context.user_id
    assert body["project_id"] == context.project_id
    assert body["dataset_id"] == "ds_btcusdt_perp_2024_q1"
    assert body["catalog_path"].startswith(tmp_path.as_posix())
    assert body["data_type"] == "quote_ticks"
    assert body["timeframe"] == "1m"
    assert body["market_type"] == "crypto_perp"


def test_strict_backtest_job_creation_requires_auth_context(tmp_path) -> None:
    context = _strict_context()
    registry = _strict_dataset_registry(tmp_path, context)

    payload = _strict_payload()
    response = create_backtest_job_payload(
        BacktestJobService(),
        payload,
        context=None,
        dataset_registry=registry,
        strict_scope=True,
    )

    assert response.status_code == 401
    assert response.json()["error"] == "auth_required"


def test_strict_backtest_job_creation_returns_422_for_missing_required_fields(tmp_path) -> None:
    context = _strict_context()
    registry = _strict_dataset_registry(tmp_path, context)
    payload = _strict_payload()
    payload.pop("data_type")

    response = create_backtest_job_payload(
        BacktestJobService(),
        payload,
        context=context,
        dataset_registry=registry,
        strict_scope=True,
    )

    assert response.status_code == 422
    assert response.json()["error"] == "invalid_backtest_job_request"
    assert "data_type" in response.json()["details"]


def test_strict_backtest_job_creation_validates_market_profile_and_dataset_before_creation(tmp_path) -> None:
    context = _strict_context()
    registry = _strict_dataset_registry(tmp_path, context)
    payload = {**_strict_payload(), "data_type": "historical_bars"}

    response = create_backtest_job_payload(
        BacktestJobService(),
        payload,
        context=context,
        dataset_registry=registry,
        strict_scope=True,
    )

    assert response.status_code == 422
    assert response.json()["error"] == "invalid_backtest_job_request"
    assert "dataset field mismatch: data_type expected historical_bars, got quote_ticks" in response.json()["details"]


def test_strict_backtest_job_read_and_cancel_ignore_spoofed_query_scope(tmp_path) -> None:
    context = _strict_context()
    registry = _strict_dataset_registry(tmp_path, context)
    service = BacktestJobService()
    created = create_backtest_job_payload(
        service,
        _strict_payload(),
        context=context,
        dataset_registry=registry,
        strict_scope=True,
    )
    job_id = created.json()["job_id"]

    detail = backtest_job_payload(
        service,
        job_id,
        context=context,
        user_id="attacker",
        project_id="evil_project",
        strict_scope=True,
    )
    cancelled = cancel_backtest_job_payload(
        service,
        job_id,
        context=context,
        user_id="attacker",
        project_id="evil_project",
        strict_scope=True,
    )
    intruder = backtest_job_payload(
        service,
        job_id,
        context=UserProjectContext(user_id="user_123", project_id="project_beta"),
        strict_scope=True,
    )

    assert detail.status_code == 200
    assert detail.json()["project_id"] == context.project_id
    assert cancelled.status_code == 200
    assert cancelled.json()["status"] == "cancel_requested"
    assert intruder.status_code == 403
    assert intruder.json()["error"] == "forbidden"


def test_strict_backtest_job_creation_requires_root_policy_registry(tmp_path) -> None:
    context = _strict_context()
    registry = CatalogDatasetRegistryService(allow_unrooted_test_mode=True)
    registry.register_dataset(
        CatalogDataset(
            dataset_id="ds_btcusdt_perp_2024_q1",
            user_id=context.user_id,
            project_id=context.project_id,
            adapter_id="BINANCE_PERP",
            instrument_id="BTCUSDT-PERP",
            data_type="quote_ticks",
            timeframe="1m",
            market_type="crypto_perp",
            date_range="2024-01-01:2024-03-01",
            catalog_path=(tmp_path / "catalogs" / "ds_btcusdt_perp_2024_q1").as_posix(),
        )
    )

    response = create_backtest_job_payload(
        BacktestJobService(),
        _strict_payload(),
        context=context,
        dataset_registry=registry,
        strict_scope=True,
    )

    assert response.status_code == 422
    assert response.json()["error"] == "invalid_backtest_job_request"
    assert "catalog_root is required" in response.json()["details"]


def test_strict_backtest_job_creation_requires_explicit_sha256_compile_hash(tmp_path) -> None:
    context = _strict_context()
    registry = _strict_dataset_registry(tmp_path, context)
    payload = _strict_payload()
    payload.pop("compile_hash")
    response = create_backtest_job_payload(
        BacktestJobService(),
        payload,
        context=context,
        dataset_registry=registry,
        strict_scope=True,
    )

    assert response.status_code == 422
    assert "compile_hash" in response.json()["details"]


def test_strict_backtest_job_creation_keeps_compile_artifact_id_separate_from_hash(tmp_path) -> None:
    context = _strict_context()
    registry = _strict_dataset_registry(tmp_path, context)
    payload = {**_strict_payload(), "compile_hash": "a" * 64, "compile_artifact_id": "compile_001"}

    response = create_backtest_job_payload(
        BacktestJobService(),
        payload,
        context=context,
        dataset_registry=registry,
        strict_scope=True,
    )

    assert response.status_code == 201
    body = response.json()
    assert body["compile_hash"] == "a" * 64
    assert body["compile_artifact_id"] == "compile_001"
