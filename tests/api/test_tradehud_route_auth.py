"""P0-1 regression: TradeHUD routes must be route-level authenticated + rate-limited.

TradeHUD is observational/read-only, but it exposes operational state, runtime
health, signal previews, gate decisions, execution reports, and Redis-backed feed
status. It must remain downstream-of-auth: every /api/tradehud/* route enforces
auth + rate limit exactly like the other /api/* routes, and the SSE stream never
starts before auth passes.
"""
from __future__ import annotations

import sys
import types

import pytest

from tests.api.test_fastapi_app import _FakeFastAPI, _FakeJSONResponse


class _FakeStreamingResponse:
    def __init__(self, content=(), *args, **kwargs) -> None:
        self.content = content
        self.headers = kwargs.get("headers", {})
        self.media_type = kwargs.get("media_type")
        self.status_code = kwargs.get("status_code", 200)
        # Do NOT eagerly drain an async generator; real SSE bodies are async.
        # We only need to observe that a streaming response was constructed.
        self.started = True


class _DenyAllRateLimiter:
    def __init__(self) -> None:
        self.keys: list[str] = []

    def is_allowed(self, key: str) -> bool:
        self.keys.append(key)
        return False


def _install_fake_fastapi(monkeypatch: pytest.MonkeyPatch) -> None:
    fake = types.SimpleNamespace(FastAPI=_FakeFastAPI, Header=lambda default=None: default)
    monkeypatch.setitem(sys.modules, "fastapi", fake)
    monkeypatch.setitem(
        sys.modules,
        "fastapi.responses",
        types.SimpleNamespace(JSONResponse=_FakeJSONResponse, StreamingResponse=_FakeStreamingResponse),
    )


TRADEHUD_ROUTES = [
    ("GET", "/api/tradehud/snapshot"),
    ("GET", "/api/tradehud/health"),
    ("GET", "/api/tradehud/events/replay"),
    ("GET", "/api/tradehud/stream"),
]


def _status(response: object) -> int:
    return getattr(response, "status_code", 200)


def test_tradehud_routes_reject_missing_auth(monkeypatch: pytest.MonkeyPatch) -> None:
    _install_fake_fastapi(monkeypatch)
    from services.api.fastapi_app import create_fastapi_app

    app = create_fastapi_app()
    failures: list[str] = []
    for method, path in TRADEHUD_ROUTES:
        handler = app.routes[(method, path)]
        response = handler()  # no authorization
        status = _status(response)
        if status != 401:
            failures.append(f"{method} {path} -> {status}")
    assert failures == [], f"TradeHUD routes not auth-gated: {failures}"


def test_tradehud_routes_succeed_when_authenticated(monkeypatch: pytest.MonkeyPatch) -> None:
    _install_fake_fastapi(monkeypatch)
    from packages.auth import AuthTokenService
    from services.api.fastapi_app import create_fastapi_app

    auth = AuthTokenService()
    token = auth.issue_token(user_id="user_123", project_id="project_alpha")
    app = create_fastapi_app(auth_token_service=auth)

    bearer = f"Bearer {token.token}"
    for method, path in TRADEHUD_ROUTES:
        handler = app.routes[(method, path)]
        response = handler(authorization=bearer)
        # Auth passed; the route returned its real payload (dict) or a
        # StreamingResponse (200). We assert auth did not short-circuit.
        assert _status(response) == 200, f"{method} {path} -> {_status(response)}"
        assert not isinstance(response, _FakeJSONResponse), f"{method} {path} returned an error JSON"


def test_tradehud_routes_enforce_rate_limit_after_auth(monkeypatch: pytest.MonkeyPatch) -> None:
    _install_fake_fastapi(monkeypatch)
    from packages.auth import AuthTokenService
    from services.api.fastapi_app import create_fastapi_app

    auth = AuthTokenService()
    token = auth.issue_token(user_id="user_123", project_id="project_alpha")
    limiter = _DenyAllRateLimiter()
    app = create_fastapi_app(auth_token_service=auth, rate_limiter=limiter)

    bearer = f"Bearer {token.token}"
    failures: list[str] = []
    for method, path in TRADEHUD_ROUTES:
        handler = app.routes[(method, path)]
        response = handler(authorization=bearer)
        if _status(response) != 429:
            failures.append(f"{method} {path} -> {_status(response)}")
    assert failures == [], f"TradeHUD routes not rate-limited: {failures}"
    # All four must key on the authenticated context.
    assert limiter.keys == ["user_123:project_alpha"] * 4


def test_tradehud_stream_does_not_start_before_auth(monkeypatch: pytest.MonkeyPatch) -> None:
    """An unauthenticated SSE request must return the auth error and must NOT
    construct/start the streaming response (no generator side effects)."""
    _install_fake_fastapi(monkeypatch)
    from services.api.fastapi_app import create_fastapi_app

    app = create_fastapi_app()
    response = app.routes[("GET", "/api/tradehud/stream")]()
    # Auth error, not a 200 stream.
    assert _status(response) == 401
    assert not isinstance(response, _FakeStreamingResponse), "stream started before auth"
