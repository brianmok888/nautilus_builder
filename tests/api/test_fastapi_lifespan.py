"""P1-4 regression: FastAPI startup guard migrated from on_event to lifespan.

FastAPI deprecated @app.on_event("startup"); startup/shutdown logic must live in a
lifespan context manager. The evidence-storage revalidation must still run at
startup with identical fail-closed behavior. This test asserts the app is built
with a lifespan handler and that the _FakeFastAPI stub is no longer asked to
register an on_event hook.
"""
from __future__ import annotations

import sys
import types

import pytest

from tests.api.test_fastapi_app import _FakeFastAPI, _FakeJSONResponse, _FakeStreamingResponse


def _install_fake_fastapi(monkeypatch: pytest.MonkeyPatch) -> None:
    fake = types.SimpleNamespace(FastAPI=_FakeFastAPI, Header=lambda default=None: default)
    monkeypatch.setitem(sys.modules, "fastapi", fake)
    monkeypatch.setitem(
        sys.modules,
        "fastapi.responses",
        types.SimpleNamespace(JSONResponse=_FakeJSONResponse, StreamingResponse=_FakeStreamingResponse),
    )


def test_app_is_built_with_lifespan(monkeypatch: pytest.MonkeyPatch) -> None:
    _install_fake_fastapi(monkeypatch)
    from services.api.fastapi_app import create_fastapi_app

    app = create_fastapi_app()

    # The stub records whether a lifespan was passed and whether on_event was used.
    assert getattr(app, "lifespan_passed", False) is True, "FastAPI must be built with a lifespan handler"
    assert getattr(app, "on_event_used", False) is False, "must not use deprecated @app.on_event"

