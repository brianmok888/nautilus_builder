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

    def add_middleware(self, middleware_cls, **kwargs):
        pass  # no-op for tests


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
    assert ("POST", "/api/backtest-jobs/{job_id}/run") in app.routes


def test_fastapi_bootstrap_reuses_route_payload_helpers(monkeypatch) -> None:
    from packages.auth import AuthTokenService

    fake_fastapi_module = types.SimpleNamespace(FastAPI=_FakeFastAPI, Header=lambda default=None: default)
    monkeypatch.setitem(sys.modules, "fastapi", fake_fastapi_module)
    monkeypatch.setitem(sys.modules, "fastapi.responses", types.SimpleNamespace(JSONResponse=_FakeJSONResponse))

    from services.api.fastapi_app import create_fastapi_app

    auth = AuthTokenService()
    token = auth.issue_token(user_id="user_123", project_id="project_alpha")
    app = create_fastapi_app(auth_token_service=auth)

    health_payload = app.routes[("GET", "/health")]()
    ai_payload = app.routes[("POST", "/api/ai-builder/draft")]({"prompt": "Draft EMA RSI"}, authorization=f"Bearer {token.token}")

    assert health_payload == {"status": "ok", "service": "nautilus_builder_api"}
    assert ai_payload.status_code == 200
    assert ai_payload.json()["spec"]["stage"] == "draft"
    assert ai_payload.json()["spec"]["validation"]["output_mode"] == "signal_preview_only"


def test_fastapi_bootstrap_reuses_strategy_repository_helpers(monkeypatch) -> None:
    from packages.auth import AuthTokenService
    from tests.strategy_spec.test_schema_valid import make_valid_spec

    fake_fastapi_module = types.SimpleNamespace(FastAPI=_FakeFastAPI, Header=lambda default=None: default)
    monkeypatch.setitem(sys.modules, "fastapi", fake_fastapi_module)
    monkeypatch.setitem(sys.modules, "fastapi.responses", types.SimpleNamespace(JSONResponse=_FakeJSONResponse))

    from services.api.fastapi_app import create_fastapi_app

    auth = AuthTokenService()
    token = auth.issue_token(user_id="user_123", project_id="project_alpha")
    app = create_fastapi_app(auth_token_service=auth)

    created = app.routes[("POST", "/api/strategies")](make_valid_spec(), authorization=f"Bearer {token.token}")
    listed = app.routes[("GET", "/api/strategies")](authorization=f"Bearer {token.token}")
    detail = app.routes[("GET", "/api/strategies/{strategy_id}")]("strategy_001", authorization=f"Bearer {token.token}")

    assert created.status_code == 201
    assert created.json()["strategy_id"] == "strategy_001"
    assert listed.status_code == 200
    assert listed.json()[0]["strategy_id"] == "strategy_001"
    assert detail.status_code == 200
    assert detail.json()["versions"][0]["spec"]["version"] == "0.1.0-draft.1"


def test_fastapi_bootstrap_preserves_error_status_codes(monkeypatch) -> None:
    from packages.auth import AuthTokenService

    fake_fastapi_module = types.SimpleNamespace(FastAPI=_FakeFastAPI, Header=lambda default=None: default)
    monkeypatch.setitem(sys.modules, "fastapi", fake_fastapi_module)
    monkeypatch.setitem(sys.modules, "fastapi.responses", types.SimpleNamespace(JSONResponse=_FakeJSONResponse))

    from services.api.fastapi_app import create_fastapi_app

    auth = AuthTokenService()
    token = auth.issue_token(user_id="user_123", project_id="project_alpha")
    app = create_fastapi_app(auth_token_service=auth)

    missing = app.routes[("GET", "/api/strategies/{strategy_id}")]("missing", authorization=f"Bearer {token.token}")
    rejected = app.routes[("POST", "/api/promotions/request")](
        {"strategy_version_id": "v1", "result_id": "res1", "target": "live"},
        authorization=f"Bearer {token.token}",
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
        "compile_hash": "a" * 64,
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
            payload={
                "evidence_type": key,
                "compile_hash": "abc123",
                "strategy_version": "0.3.0-beta.1",
                "orders": 0,
            },
            metadata={"compile_hash": "abc123", "strategy_version": "0.3.0-beta.1"},
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


def test_fastapi_strategy_routes_require_auth_and_filter_by_project(monkeypatch) -> None:
    from packages.auth import AuthTokenService
    from tests.strategy_spec.test_schema_valid import make_valid_spec

    fake_fastapi_module = types.SimpleNamespace(FastAPI=_FakeFastAPI, Header=lambda default=None: default)
    monkeypatch.setitem(sys.modules, "fastapi", fake_fastapi_module)
    monkeypatch.setitem(sys.modules, "fastapi.responses", types.SimpleNamespace(JSONResponse=_FakeJSONResponse))

    from services.api.fastapi_app import create_fastapi_app

    auth = AuthTokenService()
    alpha = auth.issue_token(user_id="user_123", project_id="project_alpha")
    beta = auth.issue_token(user_id="user_456", project_id="project_beta")
    app = create_fastapi_app(auth_token_service=auth)

    missing_create = app.routes[("POST", "/api/strategies")](make_valid_spec())
    created = app.routes[("POST", "/api/strategies")](make_valid_spec(), authorization=f"Bearer {alpha.token}")
    missing_list = app.routes[("GET", "/api/strategies")]()
    listed_beta = app.routes[("GET", "/api/strategies")](authorization=f"Bearer {beta.token}")
    listed_alpha = app.routes[("GET", "/api/strategies")](authorization=f"Bearer {alpha.token}")
    detail_beta = app.routes[("GET", "/api/strategies/{strategy_id}")](
        "strategy_001",
        authorization=f"Bearer {beta.token}",
    )

    assert missing_create.status_code == 401
    assert created.status_code == 201
    assert created.json()["project_id"] == "project_alpha"
    assert missing_list.status_code == 401
    assert listed_beta.status_code == 200
    assert listed_beta.json() == []
    assert listed_alpha.status_code == 200
    assert listed_alpha.json()[0]["strategy_id"] == "strategy_001"
    assert detail_beta.status_code == 403
    assert detail_beta.json()["error"] == "forbidden"


def test_fastapi_strategy_approve_and_clone_are_project_scoped(monkeypatch) -> None:
    from packages.auth import AuthTokenService
    from tests.strategy_spec.test_schema_valid import make_valid_spec

    fake_fastapi_module = types.SimpleNamespace(FastAPI=_FakeFastAPI, Header=lambda default=None: default)
    monkeypatch.setitem(sys.modules, "fastapi", fake_fastapi_module)
    monkeypatch.setitem(sys.modules, "fastapi.responses", types.SimpleNamespace(JSONResponse=_FakeJSONResponse))

    from services.api.fastapi_app import create_fastapi_app

    auth = AuthTokenService()
    alpha = auth.issue_token(user_id="user_123", project_id="project_alpha")
    beta = auth.issue_token(user_id="user_456", project_id="project_beta")
    app = create_fastapi_app(auth_token_service=auth)
    backtested_spec = {**make_valid_spec(), "status": "backtested"}
    created = app.routes[("POST", "/api/strategies")](backtested_spec, authorization=f"Bearer {alpha.token}")
    strategy_id = created.json()["strategy_id"]

    beta_approve = app.routes[("POST", "/api/strategies/{strategy_id}/approve")](
        strategy_id,
        authorization=f"Bearer {beta.token}",
    )
    beta_clone = app.routes[("POST", "/api/strategies/{strategy_id}/clone")](
        strategy_id,
        authorization=f"Bearer {beta.token}",
    )
    alpha_approve = app.routes[("POST", "/api/strategies/{strategy_id}/approve")](
        strategy_id,
        authorization=f"Bearer {alpha.token}",
    )
    alpha_clone = app.routes[("POST", "/api/strategies/{strategy_id}/clone")](
        strategy_id,
        authorization=f"Bearer {alpha.token}",
    )

    assert beta_approve.status_code == 403
    assert beta_approve.json()["error"] == "forbidden"
    assert beta_clone.status_code == 403
    assert beta_clone.json()["error"] == "forbidden"
    assert alpha_approve.status_code == 200
    assert alpha_approve.json()["status"] == "approved"
    assert alpha_clone.status_code == 201
    assert alpha_clone.json()["project_id"] == "project_alpha"


def test_fastapi_workflow_routes_require_auth_and_deny_cross_project(monkeypatch) -> None:
    from packages.auth import AuthTokenService
    from packages.workflow_spine import AiSuggestionRecord, InMemoryWorkflowRepository, WorkflowResultRecord

    fake_fastapi_module = types.SimpleNamespace(FastAPI=_FakeFastAPI, Header=lambda default=None: default)
    monkeypatch.setitem(sys.modules, "fastapi", fake_fastapi_module)
    monkeypatch.setitem(sys.modules, "fastapi.responses", types.SimpleNamespace(JSONResponse=_FakeJSONResponse))

    from services.api.fastapi_app import create_fastapi_app

    repository = InMemoryWorkflowRepository()
    repository.save_result(
        WorkflowResultRecord(
            result_id="res_alpha",
            test_job_id="job_alpha",
            project_id="project_alpha",
            strategy_lineage_id="lineage_alpha",
            strategy_version_id="sv_alpha",
            metrics={"sharpe": 1.0},
            artifact_refs={"result": "artifact://builder/project_alpha/user_123/backtest_result/res_alpha"},
        )
    )
    repository.save_ai_suggestion(
        AiSuggestionRecord(
            suggestion_id="sug_alpha",
            project_id="project_alpha",
            strategy_lineage_id="lineage_alpha",
            strategy_version_id="sv_alpha",
            result_id="res_alpha",
            ai_thread_id="thread_alpha",
            improvement_cycle_id="cycle_alpha",
            suggestion_type="parameter_adjustment",
            message="Retest lower RSI threshold.",
        )
    )
    auth = AuthTokenService()
    alpha = auth.issue_token(user_id="user_123", project_id="project_alpha")
    beta = auth.issue_token(user_id="user_456", project_id="project_beta")
    app = create_fastapi_app(workflow_repository=repository, auth_token_service=auth)

    missing = app.routes[("GET", "/api/workflow/results/{result_id}")]("res_alpha")
    alpha_result = app.routes[("GET", "/api/workflow/results/{result_id}")]("res_alpha", authorization=f"Bearer {alpha.token}")
    beta_result = app.routes[("GET", "/api/workflow/results/{result_id}")]("res_alpha", authorization=f"Bearer {beta.token}")
    beta_suggestions = app.routes[("GET", "/api/workflow/results/{result_id}/suggestions")](
        "res_alpha",
        authorization=f"Bearer {beta.token}",
    )
    beta_list = app.routes[("GET", "/api/results")](authorization=f"Bearer {beta.token}")
    beta_lineage = app.routes[("GET", "/api/workflow/lineages/{strategy_lineage_id}/status")](
        "lineage_alpha",
        authorization=f"Bearer {beta.token}",
    )

    assert missing.status_code == 401
    assert alpha_result.status_code == 200
    assert alpha_result.json()["project_id"] == "project_alpha"
    assert beta_result.status_code == 403
    assert beta_list.status_code == 200
    assert beta_list.json() == []
    assert beta_suggestions.status_code == 403
    assert beta_lineage.status_code == 403


def test_fastapi_demo_seed_uses_default_dev_token_scope(monkeypatch) -> None:
    from packages.auth import AuthTokenService

    fake_fastapi_module = types.SimpleNamespace(FastAPI=_FakeFastAPI, Header=lambda default=None: default)
    monkeypatch.setitem(sys.modules, "fastapi", fake_fastapi_module)
    monkeypatch.setitem(sys.modules, "fastapi.responses", types.SimpleNamespace(JSONResponse=_FakeJSONResponse))
    monkeypatch.setenv("BUILDER_SEED_DEMO_STRATEGIES", "1")
    monkeypatch.setenv("BUILDER_API_TOKEN", "local-demo-token")
    monkeypatch.delenv("BUILDER_DATABASE_URL", raising=False)

    from services.api.fastapi_app import create_fastapi_app

    auth = AuthTokenService()
    app = create_fastapi_app(auth_token_service=auth)

    summary = app.routes[("GET", "/api/strategies/{strategy_id}/evidence-summary")](
        "demo_replay_passed",
        authorization="Bearer local-demo-token",
    )

    assert summary.status_code == 200
    assert summary.json()["strategyId"] == "demo_replay_passed"


def test_fastapi_runtime_ai_and_promotion_request_routes_require_auth(monkeypatch) -> None:
    from packages.auth import AuthTokenService

    fake_fastapi_module = types.SimpleNamespace(FastAPI=_FakeFastAPI, Header=lambda default=None: default)
    monkeypatch.setitem(sys.modules, "fastapi", fake_fastapi_module)
    monkeypatch.setitem(sys.modules, "fastapi.responses", types.SimpleNamespace(JSONResponse=_FakeJSONResponse))

    from services.api.fastapi_app import create_fastapi_app

    auth = AuthTokenService()
    token = auth.issue_token(user_id="user_123", project_id="project_alpha")
    app = create_fastapi_app(auth_token_service=auth)

    missing_runtime = app.routes[("GET", "/api/runtime-events/replay")]()
    missing_ai = app.routes[("POST", "/api/ai-builder/draft")]({"prompt": "Draft EMA RSI"})
    missing_promotion = app.routes[("POST", "/api/promotions/request")](
        {"strategy_version_id": "v1", "result_id": "res1", "target": "shadow"}
    )
    runtime = app.routes[("GET", "/api/runtime-events/replay")](authorization=f"Bearer {token.token}")
    ai = app.routes[("POST", "/api/ai-builder/draft")]({"prompt": "Draft EMA RSI"}, authorization=f"Bearer {token.token}")
    promotion = app.routes[("POST", "/api/promotions/request")](
        {"strategy_version_id": "v1", "result_id": "res1", "target": "shadow"},
        authorization=f"Bearer {token.token}",
    )

    assert missing_runtime.status_code == 401
    assert missing_ai.status_code == 401
    assert missing_promotion.status_code == 401
    assert runtime.status_code == 200
    assert ai.status_code == 200
    assert promotion.status_code == 201


def test_fastapi_ai_apply_requires_provenance_and_uses_injected_audit_store(monkeypatch) -> None:
    import sqlite3

    from packages.ai_builder.provider import SqliteAiDraftAuditStore
    from packages.auth import AuthTokenService

    fake_fastapi_module = types.SimpleNamespace(FastAPI=_FakeFastAPI, Header=lambda default=None: default)
    monkeypatch.setitem(sys.modules, "fastapi", fake_fastapi_module)
    monkeypatch.setitem(sys.modules, "fastapi.responses", types.SimpleNamespace(JSONResponse=_FakeJSONResponse))

    from services.api.fastapi_app import create_fastapi_app

    connection = sqlite3.connect(":memory:")
    audit_store = SqliteAiDraftAuditStore(connection=connection)
    auth = AuthTokenService()
    token = auth.issue_token(user_id="user_123", project_id="project_alpha")
    app = create_fastapi_app(auth_token_service=auth, ai_audit_store=audit_store)
    payload = {
        "prompt": "Create EMA RSI",
        "ai_thread_id": "ai_thread_001",
        "improvement_cycle_id": "cycle_001",
        "strategy_lineage_id": "lineage_strategy_001",
        "strategy_version_id": "strategy_001_v002",
    }

    blank = app.routes[("POST", "/api/ai-builder/apply")]({**payload, "ai_thread_id": ""}, authorization=f"Bearer {token.token}")
    applied = app.routes[("POST", "/api/ai-builder/apply")](payload, authorization=f"Bearer {token.token}")
    reloaded = SqliteAiDraftAuditStore(connection=connection)

    assert blank.status_code == 422
    assert "ai_thread_id is required" in blank.json()["details"]
    assert applied.status_code == 200
    assert applied.json()["mode"] == "advisory_only"
    records = reloaded.records_for_thread("ai_thread_001")
    assert any(record.get("improvement_cycle_id") == "cycle_001" for record in records)


def test_fastapi_results_route_does_not_expose_fixture_fallback_as_production_result(monkeypatch) -> None:
    from packages.auth import AuthTokenService

    fake_fastapi_module = types.SimpleNamespace(FastAPI=_FakeFastAPI, Header=lambda default=None: default)
    monkeypatch.setitem(sys.modules, "fastapi", fake_fastapi_module)
    monkeypatch.setitem(sys.modules, "fastapi.responses", types.SimpleNamespace(JSONResponse=_FakeJSONResponse))

    from services.api.fastapi_app import create_fastapi_app

    auth = AuthTokenService()
    token = auth.issue_token(user_id="user_123", project_id="project_alpha")
    app = create_fastapi_app(auth_token_service=auth)

    response = app.routes[("GET", "/api/results/{result_id}")]("res_001", authorization=f"Bearer {token.token}")

    assert response.status_code == 404
    assert response.json()["error"] == "result_not_found"


def test_fastapi_bootstrap_registers_env_dev_bearer_token(monkeypatch) -> None:
    fake_fastapi_module = types.SimpleNamespace(FastAPI=_FakeFastAPI, Header=lambda default=None: default)
    monkeypatch.setitem(sys.modules, "fastapi", fake_fastapi_module)
    monkeypatch.setitem(sys.modules, "fastapi.responses", types.SimpleNamespace(JSONResponse=_FakeJSONResponse))
    monkeypatch.setenv("BUILDER_DEV_AUTH_TOKEN", "nb_local_dev_token")
    monkeypatch.setenv("BUILDER_DEV_USER_ID", "user_123")
    monkeypatch.setenv("BUILDER_DEV_PROJECT_ID", "project_alpha")

    from services.api.fastapi_app import create_fastapi_app

    app = create_fastapi_app()
    response = app.routes[("POST", "/api/ai-builder/draft")](
        {"prompt": "Draft EMA RSI"},
        authorization="Bearer nb_local_dev_token",
    )

    assert response.status_code == 200
    assert response.json()["accepted"] is True


def test_fastapi_backtest_run_route_ignores_client_worker_identity(monkeypatch) -> None:
    from packages.auth import AuthTokenService
    from packages.auth import UserProjectContext
    from packages.backtest_jobs.service import BacktestJobService
    from packages.runtime_events.service import RuntimeEventService

    fake_fastapi_module = types.SimpleNamespace(FastAPI=_FakeFastAPI, Header=lambda default=None: default)
    monkeypatch.setitem(sys.modules, "fastapi", fake_fastapi_module)
    monkeypatch.setitem(sys.modules, "fastapi.responses", types.SimpleNamespace(JSONResponse=_FakeJSONResponse))

    from services.api.fastapi_app import create_fastapi_app

    auth = AuthTokenService()
    token = auth.issue_token(user_id="user_123", project_id="project_alpha")
    context = UserProjectContext(user_id="user_123", project_id="project_alpha")
    jobs = BacktestJobService()
    events = RuntimeEventService()
    job = jobs.create_job(
        {
            "strategy_spec_version_id": "strategy_001_v001",
            "adapter_profile_id": "BINANCE_PERP",
            "instrument_id": "BTCUSDT-PERP",
            "compile_hash": "a" * 64,
            "validation_report_id": "validation_001",
            "user_id": context.user_id,
            "project_id": context.project_id,
        }
    )
    jobs.request_cancel(job.job_id, context=context)
    app = create_fastapi_app(auth_token_service=auth, backtest_job_service=jobs, runtime_event_service=events)

    response = app.routes[("POST", "/api/backtest-jobs/{job_id}/run")](
        job.job_id,
        {"worker_image": "attacker-controlled-worker"},
        authorization=f"Bearer {token.token}",
    )

    assert response.status_code == 200
    assert response.json()["result"] is None
    assert events.replay_events(job.job_id)[0].actor_id == "nautilus-builder-backtest-worker:local"


def test_fastapi_backtest_job_events_require_auth_and_project_scope(monkeypatch) -> None:
    from packages.auth import AuthTokenService
    from packages.backtest_jobs.service import BacktestJobService
    from packages.runtime_events.service import RuntimeEventService

    fake_fastapi_module = types.SimpleNamespace(FastAPI=_FakeFastAPI, Header=lambda default=None: default)
    monkeypatch.setitem(sys.modules, "fastapi", fake_fastapi_module)
    monkeypatch.setitem(sys.modules, "fastapi.responses", types.SimpleNamespace(JSONResponse=_FakeJSONResponse))

    from services.api.fastapi_app import create_fastapi_app

    auth = AuthTokenService()
    alpha = auth.issue_token(user_id="user_123", project_id="project_alpha")
    beta = auth.issue_token(user_id="user_456", project_id="project_beta")
    jobs = BacktestJobService()
    events = RuntimeEventService()
    job = jobs.create_job(
        {
            "strategy_spec_version_id": "strategy_001_v001",
            "adapter_profile_id": "BINANCE_PERP",
            "instrument_id": "BTCUSDT-PERP",
            "compile_hash": "a" * 64,
            "validation_report_id": "validation_001",
            "user_id": "user_123",
            "project_id": "project_alpha",
        }
    )
    events.append_event(
        job_id=job.job_id,
        stage="RUNNING",
        level="INFO",
        message="Backtest worker started",
        progress_pct=1.0,
        actor_type="worker",
        actor_id="nautilus-builder-backtest-worker:local",
    )
    app = create_fastapi_app(auth_token_service=auth, backtest_job_service=jobs, runtime_event_service=events)

    missing = app.routes[("GET", "/api/backtest-jobs/{job_id}/events")](job.job_id)
    cross_scope = app.routes[("GET", "/api/backtest-jobs/{job_id}/events")](
        job.job_id,
        authorization=f"Bearer {beta.token}",
    )
    same_scope = app.routes[("GET", "/api/backtest-jobs/{job_id}/events")](
        job.job_id,
        authorization=f"Bearer {alpha.token}",
    )

    assert missing.status_code == 401
    assert cross_scope.status_code == 403
    assert same_scope.status_code == 200
    assert same_scope.json()["events"][0]["stage"] == "RUNNING"


def test_fastapi_execution_lane_credential_slot_requires_auth_and_project_scope(monkeypatch, tmp_path) -> None:
    from packages.auth import AuthTokenService
    from packages.execution_lane import ExecutionLaneService

    fake_fastapi_module = types.SimpleNamespace(FastAPI=_FakeFastAPI, Header=lambda default=None: default)
    monkeypatch.setitem(sys.modules, "fastapi", fake_fastapi_module)
    monkeypatch.setitem(sys.modules, "fastapi.responses", types.SimpleNamespace(JSONResponse=_FakeJSONResponse))

    from services.api.fastapi_app import create_fastapi_app

    auth = AuthTokenService()
    token = auth.issue_token(user_id="user_123", project_id="project_alpha")
    service = ExecutionLaneService(credential_env_dir=tmp_path)
    app = create_fastapi_app(auth_token_service=auth, execution_lane_service=service)
    payload = {
        "tenant_id": "tenant_a",
        "project_id": "project_beta",
        "runtime_profile_id": "rp_paper_tradingnode",
        "adapter_id": "BINANCE_PERP",
        "venue": "BINANCE",
        "lane_mode": "paper",
        "requested_by": "ops_user",
        "credential_values": {"BINANCE_API_KEY": "test-binance-key"},
    }

    missing = app.routes[("POST", "/api/execution-lane/credential-slots")](payload)
    cross_scope = app.routes[("POST", "/api/execution-lane/credential-slots")](
        payload,
        authorization=f"Bearer {token.token}",
    )
    same_scope = app.routes[("POST", "/api/execution-lane/credential-slots")](
        {**payload, "project_id": "project_alpha"},
        authorization=f"Bearer {token.token}",
    )

    assert missing.status_code == 401
    assert cross_scope.status_code == 403
    assert cross_scope.json()["error"] == "project_scope_mismatch"
    assert same_scope.status_code == 201
    assert "test-binance-key" not in str(same_scope.json())


def test_fastapi_execution_lane_session_start_requires_auth_and_project_scope(monkeypatch, tmp_path) -> None:
    from packages.auth import AuthTokenService
    from packages.execution_lane import ExecutionLaneService

    fake_fastapi_module = types.SimpleNamespace(FastAPI=_FakeFastAPI, Header=lambda default=None: default)
    monkeypatch.setitem(sys.modules, "fastapi", fake_fastapi_module)
    monkeypatch.setitem(sys.modules, "fastapi.responses", types.SimpleNamespace(JSONResponse=_FakeJSONResponse))

    from services.api.fastapi_app import create_fastapi_app

    auth = AuthTokenService()
    alpha = auth.issue_token(user_id="user_alpha", project_id="project_alpha")
    beta = auth.issue_token(user_id="user_beta", project_id="project_beta")
    service = ExecutionLaneService(credential_env_dir=tmp_path)
    slot = service.create_credential_slot(
        {
            "tenant_id": "tenant_a",
            "project_id": "project_alpha",
            "runtime_profile_id": "rp_paper_tradingnode",
            "adapter_id": "BINANCE_PERP",
            "venue": "BINANCE",
            "lane_mode": "paper",
            "requested_by": "ops_user",
            "credential_values": {"BINANCE_API_KEY": "test-binance-key", "BINANCE_API_SECRET": "test-binance-secret"},
        }
    )
    service.register_profile(
        {
            "tenant_id": "tenant_a",
            "project_id": "project_alpha",
            "runtime_profile_id": "rp_paper_tradingnode",
            "profile_name": "Paper TradingNode lane",
            "lane_mode": "paper",
            "enabled": True,
            "paper_trading_enabled": True,
            "adapter_id": "BINANCE_PERP",
            "venue": "BINANCE",
            "venue_account_id": "SIM-BINANCE-001",
            "credential_slot_ref": slot.credential_slot_ref,
            "consumes_stream": "builder.execution.commands.paper.project_alpha.binance",
        }
    )
    command = service.enqueue_command(
        {
            "tenant_id": "tenant_a",
            "project_id": "project_alpha",
            "runtime_profile_id": "rp_paper_tradingnode",
            "lane_mode": "paper",
            "adapter_id": "BINANCE_PERP",
            "venue": "BINANCE",
            "venue_account_id": "SIM-BINANCE-001",
            "trade_action_id": "ta_paper_001",
            "source_event_id": "gate_evt_paper_001",
            "idempotency_key": "gate_evt_paper_001:ta_paper_001",
            "strategy_lineage_id": "lineage_ema_rsi",
            "strategy_version_id": "strategy_001_v004",
            "order_intent": {"side": "BUY", "instrument_id": "BTCUSDT-PERP.BINANCE", "quantity": "0.01"},
            "risk_decision": {"status": "approved", "risk_profile_id": "risk_paper_default"},
        }
    )
    app = create_fastapi_app(auth_token_service=auth, execution_lane_service=service)
    payload = {"runtime_profile_id": "rp_paper_tradingnode", "command_id": command.command_id, "project_id": "project_alpha"}

    missing = app.routes[("POST", "/api/execution-lane/sessions/start")](payload)
    cross_scope = app.routes[("POST", "/api/execution-lane/sessions/start")](payload, authorization=f"Bearer {beta.token}")
    same_scope = app.routes[("POST", "/api/execution-lane/sessions/start")](payload, authorization=f"Bearer {alpha.token}")

    assert missing.status_code == 401
    assert cross_scope.status_code == 403
    assert cross_scope.json()["error"] == "project_scope_mismatch"
    assert same_scope.status_code == 202
    assert same_scope.json()["lifecycle_status"] == "RUNNING"
    assert "test-binance-secret" not in str(same_scope.json())


def test_fastapi_execution_lane_routes_filter_runtime_state_by_project(monkeypatch, tmp_path) -> None:
    from packages.auth import AuthTokenService
    from packages.execution_lane import ExecutionLaneService

    fake_fastapi_module = types.SimpleNamespace(FastAPI=_FakeFastAPI, Header=lambda default=None: default)
    monkeypatch.setitem(sys.modules, "fastapi", fake_fastapi_module)
    monkeypatch.setitem(sys.modules, "fastapi.responses", types.SimpleNamespace(JSONResponse=_FakeJSONResponse))

    from services.api.fastapi_app import create_fastapi_app

    auth = AuthTokenService()
    alpha = auth.issue_token(user_id="user_alpha", project_id="project_alpha")
    beta = auth.issue_token(user_id="user_beta", project_id="project_beta")
    service = ExecutionLaneService(credential_env_dir=tmp_path)
    alpha_profile = {
        "tenant_id": "tenant_a",
        "project_id": "project_alpha",
        "runtime_profile_id": "rp_alpha_paper",
        "profile_name": "Alpha paper lane",
        "lane_mode": "paper",
        "enabled": True,
        "paper_trading_enabled": True,
        "adapter_id": "BINANCE_PERP",
        "venue": "BINANCE",
        "venue_account_id": "SIM-BINANCE-ALPHA",
        "consumes_stream": "builder.execution.commands.paper.project_alpha.binance",
    }
    service.register_profile(alpha_profile)
    service.enqueue_command(
        {
            "tenant_id": "tenant_a",
            "project_id": "project_alpha",
            "runtime_profile_id": "rp_alpha_paper",
            "lane_mode": "paper",
            "adapter_id": "BINANCE_PERP",
            "venue": "BINANCE",
            "venue_account_id": "SIM-BINANCE-ALPHA",
            "trade_action_id": "ta_alpha_001",
            "source_event_id": "gate_evt_alpha_001",
            "idempotency_key": "gate_evt_alpha_001:ta_alpha_001",
            "strategy_lineage_id": "lineage_alpha",
            "strategy_version_id": "strategy_alpha_v001",
            "order_intent": {"side": "BUY", "instrument_id": "BTCUSDT-PERP.BINANCE", "quantity": "0.01"},
            "risk_decision": {"status": "approved", "risk_profile_id": "risk_paper_default"},
        }
    )
    beta_profile_payload = {
        **alpha_profile,
        "project_id": "project_beta",
        "runtime_profile_id": "rp_beta_paper",
        "profile_name": "Beta paper lane",
        "venue_account_id": "SIM-BINANCE-BETA",
        "consumes_stream": "builder.execution.commands.paper.project_beta.binance",
    }
    beta_command_payload = {
        "tenant_id": "tenant_a",
        "project_id": "project_beta",
        "runtime_profile_id": "rp_alpha_paper",
        "lane_mode": "paper",
        "adapter_id": "BINANCE_PERP",
        "venue": "BINANCE",
        "venue_account_id": "SIM-BINANCE-ALPHA",
        "trade_action_id": "ta_beta_001",
        "source_event_id": "gate_evt_beta_001",
        "idempotency_key": "gate_evt_beta_001:ta_beta_001",
        "strategy_lineage_id": "lineage_beta",
        "strategy_version_id": "strategy_beta_v001",
        "order_intent": {"side": "BUY", "instrument_id": "BTCUSDT-PERP.BINANCE", "quantity": "0.01"},
        "risk_decision": {"status": "approved", "risk_profile_id": "risk_paper_default"},
    }
    app = create_fastapi_app(auth_token_service=auth, execution_lane_service=service)

    beta_status = app.routes[("GET", "/api/execution-lane/status")](authorization=f"Bearer {beta.token}")
    beta_plan = app.routes[("GET", "/api/execution-lane/runtime-plan")](
        "rp_alpha_paper",
        authorization=f"Bearer {beta.token}",
    )
    beta_worker = app.routes[("POST", "/api/execution-lane/worker/run-once")](
        {"runtime_profile_id": "rp_alpha_paper"},
        authorization=f"Bearer {beta.token}",
    )
    alpha_register_beta = app.routes[("POST", "/api/execution-lane/profiles")](
        beta_profile_payload,
        authorization=f"Bearer {alpha.token}",
    )
    alpha_enqueue_beta = app.routes[("POST", "/api/execution-lane/commands")](
        beta_command_payload,
        authorization=f"Bearer {alpha.token}",
    )

    assert beta_status["profiles"] == 0
    assert beta_status["queued_commands"] == 0
    assert beta_status["may_submit_order"] is False
    assert beta_plan.status_code == 403
    assert beta_plan.json()["error"] == "project_scope_mismatch"
    assert beta_worker.status_code == 403
    assert beta_worker.json()["error"] == "project_scope_mismatch"
    assert alpha_register_beta.status_code == 403
    assert alpha_register_beta.json()["error"] == "project_scope_mismatch"
    assert alpha_enqueue_beta.status_code == 403
    assert alpha_enqueue_beta.json()["error"] == "project_scope_mismatch"
