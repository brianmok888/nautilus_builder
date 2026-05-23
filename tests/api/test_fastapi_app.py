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
    fake_fastapi_module = types.SimpleNamespace(FastAPI=_FakeFastAPI)
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
    fake_fastapi_module = types.SimpleNamespace(FastAPI=_FakeFastAPI)
    monkeypatch.setitem(sys.modules, "fastapi", fake_fastapi_module)
    monkeypatch.setitem(sys.modules, "fastapi.responses", types.SimpleNamespace(JSONResponse=_FakeJSONResponse))

    from services.api.fastapi_app import create_fastapi_app

    app = create_fastapi_app()

    health_payload = app.routes[("GET", "/health")]()
    ai_payload = app.routes[("POST", "/api/ai-builder/draft")]({"prompt": "Draft EMA RSI"})

    assert health_payload == {"status": "ok", "service": "nautilus_builder_api"}
    assert ai_payload["spec"]["stage"] == "draft"
    assert ai_payload["spec"]["output"] == "signal_preview_only"


def test_fastapi_bootstrap_reuses_strategy_repository_helpers(monkeypatch) -> None:
    from tests.strategy_spec.test_schema_valid import make_valid_spec

    fake_fastapi_module = types.SimpleNamespace(FastAPI=_FakeFastAPI)
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
    fake_fastapi_module = types.SimpleNamespace(FastAPI=_FakeFastAPI)
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
