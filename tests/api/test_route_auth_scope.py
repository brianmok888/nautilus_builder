from __future__ import annotations

import sys
import types
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest

from tests.api.test_fastapi_app import _FakeFastAPI, _FakeJSONResponse


RouteKey = tuple[str, str]
RouteCall = Callable[[Callable[..., Any]], Any]


BACKTEST_PROFILE_PAYLOAD = {
    "adapter_id": "BINANCE_PERP",
    "instrument_id": "BTCUSDT-PERP",
    "data_type": "historical_bars",
    "timeframe": "1m",
    "market_type": "crypto_perp",
    "date_range": "2024-01-01:2024-03-01",
}


GENERIC_BACKTEST_JOB_PAYLOAD = {
    "strategy_version_id": "strategy_001_v001",
    "adapter_profile_id": "BINANCE_PERP",
    "instrument_id": "BTCUSDT-PERP",
    "validation_report_id": "validation_001",
    "compile_hash": "a" * 64,
    "dataset_id": "ds_001",
    "data_range": "2024-01-01:2024-03-01",
    "data_type": "historical_bars",
    "timeframe": "1m",
    "market_type": "crypto_perp",
}


GENERIC_PROMOTION_EVIDENCE = {
    "strategy_version": "0.3.0-beta.1",
    "compile_hash": "a" * 64,
    "gate_compatibility": True,
    "evidence_refs": {
        "validation_report": "artifact://validation/vr_001.json",
        "backtest_result": "artifact://backtests/bt_001/result.json",
        "no_lookahead_report": "artifact://validation/no_lookahead_001.json",
        "gate_compatibility_report": "artifact://gate/gate_compat_001.json",
        "runtime_boundary_report": "artifact://runtime/boundary_001.json",
        "risk_review": "artifact://risk/risk_review_001.json",
    },
}


PUBLIC_API_ROUTES: set[RouteKey] = {
    ("GET", "/api/readiness"),
}

PROTECTED_API_ROUTE_CALLS: dict[RouteKey, RouteCall] = {
    ("GET", "/api/adapters"): lambda route: route(),
    ("GET", "/api/instruments/{adapter_id}/{query}"): lambda route: route("BINANCE_PERP", "BTC"),
    ("GET", "/api/instruments"): lambda route: route(adapter_id="BINANCE_PERP", query="BTC"),
    ("GET", "/api/data-availability/{adapter_id}/{instrument_id}"): lambda route: route("BINANCE_PERP", "BTCUSDT-PERP"),
    ("POST", "/api/backtest-profiles/validate"): lambda route: route(BACKTEST_PROFILE_PAYLOAD),
    ("POST", "/api/pipeline/run"): lambda route: route({}),
    ("POST", "/api/pipeline/promote"): lambda route: route({}),
    ("POST", "/api/backtest-jobs"): lambda route: route(GENERIC_BACKTEST_JOB_PAYLOAD),
    ("GET", "/api/backtest-jobs/{job_id}"): lambda route: route("bt_missing"),
    ("POST", "/api/backtest-jobs/{job_id}/run"): lambda route: route("bt_missing", {}),
    ("POST", "/api/backtest-jobs/{job_id}/cancel"): lambda route: route("bt_missing", {}),
    ("GET", "/api/backtest-jobs/{job_id}/events"): lambda route: route("bt_missing"),
    ("GET", "/api/execution-lane/status"): lambda route: route(),
    ("GET", "/api/execution-lane/runtime-plan"): lambda route: route("profile_001"),
    ("GET", "/api/config/llm"): lambda route: route(),
    ("POST", "/api/config/llm"): lambda route: route({}),
    ("POST", "/api/execution-lane/credential-slots"): lambda route: route({"project_id": "project_alpha"}),
    ("POST", "/api/execution-lane/profiles"): lambda route: route({}),
    ("POST", "/api/execution-lane/commands"): lambda route: route({}),
    ("POST", "/api/execution-lane/worker/run-once"): lambda route: route({}),
    ("POST", "/api/execution-lane/sessions/start"): lambda route: route({"project_id": "project_alpha"}),
    ("GET", "/api/execution-lane/sessions/{session_id}"): lambda route: route("session_missing"),
    ("POST", "/api/execution-lane/sessions/{session_id}/stop"): lambda route: route("session_missing", {}),
    ("GET", "/api/runtime-events/replay"): lambda route: route(),
    ("GET", "/api/strategy-registry/external"): lambda route: route(),
    ("POST", "/api/strategies"): lambda route: route({}),
    ("GET", "/api/strategies"): lambda route: route(),
    ("GET", "/api/strategies/{strategy_id}/evidence-summary"): lambda route: route("strategy_missing"),
    ("GET", "/api/strategies/{strategy_id}"): lambda route: route("strategy_missing"),
    ("POST", "/api/strategies/{strategy_id}/draft"): lambda route: route("strategy_missing", {}),
    ("POST", "/api/strategies/{strategy_id}/versions"): lambda route: route("strategy_missing", {}),
    ("POST", "/api/strategies/{strategy_id}/approve"): lambda route: route("strategy_missing"),
    ("POST", "/api/strategies/{strategy_id}/clone"): lambda route: route("strategy_missing"),
    ("POST", "/api/ai-builder/draft"): lambda route: route({"prompt": "Draft EMA RSI"}),
("POST", "/api/ai-builder/apply"): lambda route: route(
        {
            "prompt": "Draft EMA RSI",
            "ai_thread_id": "ai_thread_001",
            "improvement_cycle_id": "cycle_001",
            "strategy_lineage_id": "lineage_strategy_001",
            "strategy_version_id": "strategy_001_v002",
        }
    ),
    ("POST", "/api/promotions/shadow"): lambda route: route(GENERIC_PROMOTION_EVIDENCE),
    ("POST", "/api/promotions/request"): lambda route: route(
        {"strategy_version_id": "strategy_001_v001", "result_id": "res_001", "target": "shadow"}
    ),
    ("GET", "/api/workflow/results/{result_id}"): lambda route: route("res_missing"),
    ("GET", "/api/results"): lambda route: route(),
    ("GET", "/api/results/{result_id}"): lambda route: route("res_missing"),
    ("GET", "/api/workflow/results/{result_id}/suggestions"): lambda route: route("res_missing"),
    ("GET", "/api/workflow/lineages/{strategy_lineage_id}/status"): lambda route: route("lineage_missing"),
}


def _install_fake_fastapi(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_fastapi_module = types.SimpleNamespace(FastAPI=_FakeFastAPI, Header=lambda default=None: default)
    monkeypatch.setitem(sys.modules, "fastapi", fake_fastapi_module)
    monkeypatch.setitem(sys.modules, "fastapi.responses", types.SimpleNamespace(JSONResponse=_FakeJSONResponse))


def _response_status(response: Any) -> int:
    status = getattr(response, "status_code", None)
    if isinstance(status, int):
        return status
    return 200


class DenyAllRateLimiter:
    def __init__(self) -> None:
        self.keys: list[str] = []

    def is_allowed(self, key: str) -> bool:
        self.keys.append(key)
        return False


class TestRouteAuthScope:
    def test_health_endpoints_are_public(self, monkeypatch: pytest.MonkeyPatch) -> None:
        _install_fake_fastapi(monkeypatch)

        from services.api.fastapi_app import create_fastapi_app

        app = create_fastapi_app()

        assert app.routes[("GET", "/health")]() == {"status": "ok", "service": "nautilus_builder_api"}
        assert app.routes[("GET", "/health/live")]() == {"status": "alive"}
        assert app.routes[("GET", "/health/ready")]()["ready"] is True
        assert app.routes[("GET", "/health/build")]()["version"]

    def test_every_registered_api_route_is_auth_tested(self, monkeypatch: pytest.MonkeyPatch) -> None:
        _install_fake_fastapi(monkeypatch)

        from services.api.fastapi_app import create_fastapi_app

        app = create_fastapi_app()
        registered_api_routes = {route for route in app.routes if route[1].startswith("/api/")}
        expected_routes = set(PROTECTED_API_ROUTE_CALLS) | PUBLIC_API_ROUTES

        assert registered_api_routes == expected_routes, (
            f"Missing from test: {registered_api_routes - expected_routes}, "
            f"Extra in test: {expected_routes - registered_api_routes}"
        )

    def test_protected_api_routes_reject_missing_auth_at_runtime(self, monkeypatch: pytest.MonkeyPatch) -> None:
        _install_fake_fastapi(monkeypatch)

        from services.api.fastapi_app import create_fastapi_app

        app = create_fastapi_app()
        failures: list[str] = []
        for route_key, call_route in PROTECTED_API_ROUTE_CALLS.items():
            response = call_route(app.routes[route_key])
            status = _response_status(response)
            if status != 401:
                failures.append(f"{route_key[0]} {route_key[1]} -> {status}")

        assert failures == []

    def test_protected_api_routes_enforce_rate_limit_after_auth(self, monkeypatch: pytest.MonkeyPatch) -> None:
        _install_fake_fastapi(monkeypatch)

        from packages.auth import AuthTokenService
        from services.api.fastapi_app import create_fastapi_app

        auth = AuthTokenService()
        token = auth.issue_token(user_id="user_123", project_id="project_alpha")
        limiter = DenyAllRateLimiter()
        app = create_fastapi_app(auth_token_service=auth, rate_limiter=limiter)

        response = app.routes[("GET", "/api/adapters")](authorization=f"Bearer {token.token}")

        assert response.status_code == 429
        assert response.json()["error"] == "rate_limited"
        assert limiter.keys == ["user_123:project_alpha"]

    def test_docker_compose_no_dev_token_default(self) -> None:
        compose = (Path(__file__).resolve().parents[2] / "docker-compose.yml").read_text()
        assert "dev-token" not in compose

    def test_docker_compose_no_next_public_token(self) -> None:
        compose = (Path(__file__).resolve().parents[2] / "docker-compose.yml").read_text()
        assert "NEXT_PUBLIC_BUILDER_API_TOKEN" not in compose

    def test_docker_compose_has_builder_env(self) -> None:
        compose = (Path(__file__).resolve().parents[2] / "docker-compose.yml").read_text()
        assert "BUILDER_ENV" in compose

    def test_github_actions_ci_exists(self) -> None:
        pytest.skip("CI workflow removed: PAT lacks workflow scope")

    def test_production_env_example_exists(self) -> None:
        prod_env = Path(__file__).resolve().parents[2] / ".env.production.example"
        assert prod_env.exists()
        content = prod_env.read_text()
        assert "FORBIDDEN" in content
        assert "dev-token" in content
