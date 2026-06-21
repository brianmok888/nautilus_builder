"""P0-2 regression: GET /api/evidence must not NameError on the authenticated path.

The route bound `_context` (underscore = unused) but the body referenced
`context.project_id`, raising NameError for every authenticated caller. This
test exercises the authenticated success path via the same _FakeFastAPI seam the
rest of the route-contract suite uses.
"""
from __future__ import annotations

import sys
import types

import pytest

from tests.api.test_fastapi_app import _FakeFastAPI, _FakeJSONResponse


class _FakeStreamingResponse:
    def __init__(self, content=(), *args, **kwargs) -> None:
        self.content = content
        self.status_code = kwargs.get("status_code", 200)


def _install_fake_fastapi(monkeypatch: pytest.MonkeyPatch) -> None:
    fake = types.SimpleNamespace(FastAPI=_FakeFastAPI, Header=lambda default=None: default)
    monkeypatch.setitem(sys.modules, "fastapi", fake)
    monkeypatch.setitem(
        sys.modules,
        "fastapi.responses",
        types.SimpleNamespace(JSONResponse=_FakeJSONResponse, StreamingResponse=_FakeStreamingResponse),
    )


def test_list_evidence_authenticated_does_not_nameerror(monkeypatch: pytest.MonkeyPatch) -> None:
    """Authenticated GET /api/evidence returns 200, not 500 from NameError."""
    _install_fake_fastapi(monkeypatch)

    from packages.auth import AuthTokenService
    from services.api.fastapi_app import create_fastapi_app

    auth = AuthTokenService()
    token = auth.issue_token(user_id="user_123", project_id="project_alpha")
    app = create_fastapi_app(auth_token_service=auth)

    response = app.routes[("GET", "/api/evidence")](authorization=f"Bearer {token.token}")

    # The buggy code raised NameError("context") which _FakeFastAPI lets
    # propagate; the fixed code returns the ApiResponse at status 200.
    status = getattr(response, "status_code", 200)
    assert status == 200, f"expected 200 evidence list, got status={status!r} body={getattr(response, 'content', response)!r}"


def test_list_evidence_is_project_scoped(monkeypatch: pytest.MonkeyPatch) -> None:
    """Returned evidence is scoped to the caller's project_id; cross-project
    evidence from another project is not returned."""
    _install_fake_fastapi(monkeypatch)

    from packages.auth import AuthTokenService
    from services.api.fastapi_app import create_fastapi_app

    auth = AuthTokenService()
    alpha = auth.issue_token(user_id="user_alpha", project_id="project_alpha")
    beta = auth.issue_token(user_id="user_beta", project_id="project_beta")
    app = create_fastapi_app(auth_token_service=auth)

    # Seed evidence in project_alpha (via the POST route with project_alpha token).
    app.routes[("POST", "/api/evidence")](
        {
            "evidence_id": "ev_alpha_001",
            "project_id": "project_alpha",
            "artifact_type": "strategy_spec",
            "source_system": "test",
            "uri": "artifact://ev/alpha",
        },
        authorization=f"Bearer {alpha.token}",
    )

    # project_beta caller should NOT see project_alpha's evidence.
    beta_response = app.routes[("GET", "/api/evidence")](authorization=f"Bearer {beta.token}")
    beta_body = getattr(beta_response, "content", beta_response)
    beta_items = beta_body.get("data", beta_body) if isinstance(beta_body, dict) else beta_body
    beta_ids = {item.get("evidence_id") for item in (beta_items or [])}
    assert "ev_alpha_001" not in beta_ids, "cross-project evidence leaked across projects"
