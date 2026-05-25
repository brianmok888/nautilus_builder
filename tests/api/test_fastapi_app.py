from __future__ import annotations

import sys
import types


class _FakeFastAPI:
    def __init__(self, *, title: str, version: str) -> None:
        self.title = title
        self.version = version
        self.routes: dict[tuple[str, str], object] = {}

    def get(self, path: str):
        def decorator(handler):
            self.routes[("GET", path)] = handler
            return handler

        return decorator

    def post(self, path: str):
        def decorator(handler):
            self.routes[("POST", path)] = handler
            return handler

        return decorator


class _FakeJSONResponse:
    def __init__(self, *, content, status_code: int) -> None:
        self.content = content
        self.status_code = status_code

    def json(self):
        return self.content



def test_fastapi_bootstrap_mounts_runtime_routes(monkeypatch) -> None:
    fake_fastapi_module = types.SimpleNamespace(FastAPI=_FakeFastAPI, Header=lambda default=None: default)
    monkeypatch.setitem(sys.modules, "fastapi", fake_fastapi_module)
    monkeypatch.setitem(sys.modules, "fastapi.responses", types.SimpleNamespace(JSONResponse=_FakeJSONResponse))

    from services.api.fastapi_app import create_fastapi_app

    app = create_fastapi_app()

    assert app.title == "Nautilus Builder API"
    assert ("GET", "/health") in app.routes
    assert ("GET", "/api/runtime-events/replay") in app.routes
    assert ("POST", "/api/ai-builder/draft") in app.routes
    assert ("POST", "/api/promotions/shadow") in app.routes
    assert ("POST", "/api/strategies") in app.routes
    assert ("GET", "/api/strategies") in app.routes
    assert ("GET", "/api/strategies/{strategy_id}") in app.routes


def test_fastapi_bootstrap_reuses_route_payload_helpers(monkeypatch) -> None:
    fake_fastapi_module = types.SimpleNamespace(FastAPI=_FakeFastAPI, Header=lambda default=None: default)
    monkeypatch.setitem(sys.modules, "fastapi", fake_fastapi_module)
    monkeypatch.setitem(sys.modules, "fastapi.responses", types.SimpleNamespace(JSONResponse=_FakeJSONResponse))

    from services.api.fastapi_app import create_fastapi_app

    app = create_fastapi_app()

    health_payload = app.routes[("GET", "/health")]()
    ai_payload = app.routes[("POST", "/api/ai-builder/draft")]({"prompt": "Draft EMA RSI"})

    assert health_payload == {"status": "ok", "service": "nautilus_builder_api"}
    assert ai_payload["spec"]["stage"] == "draft"
    assert ai_payload["spec"]["validation"]["output_mode"] == "signal_preview_only"


def test_fastapi_bootstrap_reuses_strategy_repository_helpers(monkeypatch) -> None:
    from tests.strategy_spec.test_schema_valid import make_valid_spec

    fake_fastapi_module = types.SimpleNamespace(FastAPI=_FakeFastAPI, Header=lambda default=None: default)
    monkeypatch.setitem(sys.modules, "fastapi", fake_fastapi_module)
    monkeypatch.setitem(sys.modules, "fastapi.responses", types.SimpleNamespace(JSONResponse=_FakeJSONResponse))

    from services.api.fastapi_app import create_fastapi_app

    app = create_fastapi_app()

    created = app.routes[("POST", "/api/strategies")](make_valid_spec())
    listed = app.routes[("GET", "/api/strategies")]()
    detail = app.routes[("GET", "/api/strategies/{strategy_id}")]("strategy_001")

    assert created.status_code == 201
    assert created.json()["strategy_id"] == "strategy_001"
    assert listed[0]["strategy_id"] == "strategy_001"
    assert detail.status_code == 200
    assert detail.json()["versions"][0]["spec"]["version"] == "0.1.0-draft.1"


def test_fastapi_bootstrap_preserves_error_status_codes(monkeypatch) -> None:
    fake_fastapi_module = types.SimpleNamespace(FastAPI=_FakeFastAPI, Header=lambda default=None: default)
    monkeypatch.setitem(sys.modules, "fastapi", fake_fastapi_module)
    monkeypatch.setitem(sys.modules, "fastapi.responses", types.SimpleNamespace(JSONResponse=_FakeJSONResponse))

    from services.api.fastapi_app import create_fastapi_app

    app = create_fastapi_app()

    missing = app.routes[("GET", "/api/strategies/{strategy_id}")]("missing")
    rejected = app.routes[("POST", "/api/promotions/request")](
        {"strategy_version_id": "v1", "result_id": "res1", "target": "live"}
    )

    assert missing.status_code == 404
    assert rejected.status_code == 422



def test_fastapi_backtest_jobs_require_bearer_auth_and_ignore_spoofed_scope(monkeypatch, tmp_path) -> None:
    from packages.auth import AuthTokenService, UserProjectContext
    from packages.catalog_datasets import CatalogDataset, CatalogDatasetRegistryService

    fake_fastapi_module = types.SimpleNamespace(FastAPI=_FakeFastAPI, Header=lambda default=None: default)
    monkeypatch.setitem(sys.modules, "fastapi", fake_fastapi_module)
    monkeypatch.setitem(sys.modules, "fastapi.responses", types.SimpleNamespace(JSONResponse=_FakeJSONResponse))

    from services.api.fastapi_app import create_fastapi_app

    auth = AuthTokenService()
    token = auth.issue_token(user_id="user_123", project_id="project_alpha")
    context = UserProjectContext(user_id="user_123", project_id="project_alpha")
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
    app = create_fastapi_app(auth_token_service=auth, catalog_dataset_registry=registry)
    payload = {
        "strategy_version_id": "strategy_001_v001",
        "adapter_profile_id": "BINANCE_PERP",
        "instrument_id": "BTCUSDT-PERP",
        "validation_report_id": "validation_001",
        "compile_artifact_id": "compile_001",
        "created_by": "operator_001",
        "data_range": "2024-01-01:2024-03-01",
        "data_type": "quote_ticks",
        "timeframe": "1m",
        "market_type": "crypto_perp",
        "dataset_id": "ds_btcusdt_perp_2024_q1",
        "user_id": "attacker",
        "project_id": "evil_project",
    }

    missing = app.routes[("POST", "/api/backtest-jobs")](payload)
    created = app.routes[("POST", "/api/backtest-jobs")](payload, authorization=f"Bearer {token.token}")
    job_id = created.json()["job_id"]
    detail = app.routes[("GET", "/api/backtest-jobs/{job_id}")](
        job_id,
        user_id="attacker",
        project_id="evil_project",
        authorization=f"Bearer {token.token}",
    )

    assert missing.status_code == 401
    assert missing.json()["error"] == "auth_required"
    assert created.status_code == 201
    assert created.json()["user_id"] == "user_123"
    assert created.json()["project_id"] == "project_alpha"
    assert detail.status_code == 200
    assert detail.json()["project_id"] == "project_alpha"


def test_fastapi_shadow_promotion_requires_auth_and_resolves_scoped_artifacts(monkeypatch, tmp_path) -> None:
    from packages.artifact_store import LocalJsonArtifactStore
    from packages.auth import AuthTokenService, UserProjectContext

    fake_fastapi_module = types.SimpleNamespace(FastAPI=_FakeFastAPI, Header=lambda default=None: default)
    monkeypatch.setitem(sys.modules, "fastapi", fake_fastapi_module)
    monkeypatch.setitem(sys.modules, "fastapi.responses", types.SimpleNamespace(JSONResponse=_FakeJSONResponse))

    from services.api.fastapi_app import create_fastapi_app

    auth = AuthTokenService()
    token = auth.issue_token(user_id="user_123", project_id="project_alpha")
    context = UserProjectContext(user_id="user_123", project_id="project_alpha")
    store = LocalJsonArtifactStore(root=tmp_path / "artifacts")
    refs: dict[str, str] = {}
    for key in (
        "validation_report",
        "backtest_result",
        "no_lookahead_report",
        "gate_compatibility_report",
        "runtime_boundary_report",
        "risk_review",
    ):
        refs[key] = store.put_json(
            context=context,
            artifact_type=key,
            artifact_id=f"{key}_001",
            payload={"evidence_type": key, "orders": 0},
        ).artifact_ref

    app = create_fastapi_app(auth_token_service=auth, artifact_store=store)
    payload = {
        "strategy_version": "0.3.0-beta.1",
        "compile_hash": "abc123",
        "gate_compatibility": True,
        "evidence_refs": refs,
    }

    missing = app.routes[("POST", "/api/promotions/shadow")](payload)
    created = app.routes[("POST", "/api/promotions/shadow")](payload, authorization=f"Bearer {token.token}")

    assert missing.status_code == 401
    assert missing.json()["error"] == "auth_required"
    assert created.status_code == 201
    assert set(created.json()["evidence_checksums"]) == set(refs)
