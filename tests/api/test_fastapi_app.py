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


def test_fastapi_bootstrap_mounts_runtime_routes(monkeypatch) -> None:
    fake_fastapi_module = types.SimpleNamespace(FastAPI=_FakeFastAPI)
    monkeypatch.setitem(sys.modules, "fastapi", fake_fastapi_module)

    from services.api.fastapi_app import create_fastapi_app

    app = create_fastapi_app()

    assert app.title == "Nautilus Builder API"
    assert ("GET", "/health") in app.routes
    assert ("GET", "/api/runtime-events/replay") in app.routes
    assert ("POST", "/api/ai-builder/draft") in app.routes
    assert ("POST", "/api/promotions/shadow") in app.routes


def test_fastapi_bootstrap_reuses_route_payload_helpers(monkeypatch) -> None:
    fake_fastapi_module = types.SimpleNamespace(FastAPI=_FakeFastAPI)
    monkeypatch.setitem(sys.modules, "fastapi", fake_fastapi_module)

    from services.api.fastapi_app import create_fastapi_app

    app = create_fastapi_app()

    health_payload = app.routes[("GET", "/health")]()
    ai_payload = app.routes[("POST", "/api/ai-builder/draft")]({"prompt": "Draft EMA RSI"})

    assert health_payload == {"status": "ok", "service": "nautilus_builder_api"}
    assert ai_payload["spec"]["stage"] == "draft"
    assert ai_payload["spec"]["output"] == "signal_preview_only"
