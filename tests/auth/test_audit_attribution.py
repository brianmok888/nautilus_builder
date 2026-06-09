from __future__ import annotations

from unittest.mock import MagicMock


def test_audit_middleware_records_bearer_actor_project_from_request_context() -> None:
    from fastapi import FastAPI
    from fastapi.testclient import TestClient

    from packages.auth.context_middleware import AuthContextMiddleware
    from packages.auth.service import AuthTokenService
    from packages.auth.audit_middleware import AuditMiddleware

    audit_writer = MagicMock()
    auth = AuthTokenService()
    token = auth.issue_token(user_id="user_123", project_id="project_alpha")
    app = FastAPI()
    app.add_middleware(AuditMiddleware, audit_writer=audit_writer)
    app.add_middleware(AuthContextMiddleware, auth_token_service=auth)

    @app.post("/api/strategies")
    def create_strategy() -> dict[str, str]:
        return {"status": "created"}

    response = TestClient(app).post(
        "/api/strategies",
        headers={"Authorization": f"Bearer {token.token}"},
    )

    assert response.status_code == 200
    event = audit_writer.call_args[0][0]
    assert event["actor_id"] == "user_123"
    assert event["project_id"] == "project_alpha"


def test_audit_middleware_uses_non_null_anonymous_context_for_missing_auth() -> None:
    from fastapi import FastAPI
    from fastapi.testclient import TestClient

    from packages.auth.context_middleware import AuthContextMiddleware
    from packages.auth.service import AuthTokenService
    from packages.auth.audit_middleware import AuditMiddleware

    audit_writer = MagicMock()
    app = FastAPI()
    app.add_middleware(AuditMiddleware, audit_writer=audit_writer)
    app.add_middleware(AuthContextMiddleware, auth_token_service=AuthTokenService())

    @app.post("/api/strategies")
    def create_strategy() -> dict[str, str]:
        return {"status": "created"}

    response = TestClient(app).post("/api/strategies")

    assert response.status_code == 200
    event = audit_writer.call_args[0][0]
    assert event["actor_id"] == "unauthenticated"
    assert event["project_id"] == "unknown"


def test_successful_mutation_fails_closed_when_audit_writer_fails() -> None:
    from fastapi import FastAPI
    from fastapi.testclient import TestClient

    from packages.auth.audit_middleware import AuditMiddleware

    def failing_writer(_event: dict[str, object]) -> None:
        raise RuntimeError("database unavailable")

    app = FastAPI()
    app.add_middleware(AuditMiddleware, audit_writer=failing_writer)

    @app.post("/api/strategies")
    def create_strategy() -> dict[str, str]:
        return {"status": "created"}

    response = TestClient(app).post("/api/strategies")

    assert response.status_code == 500
    assert response.json()["error"] == "audit_write_failed"


def test_failed_mutation_response_is_not_masked_when_audit_writer_fails() -> None:
    from fastapi import FastAPI
    from fastapi.responses import JSONResponse
    from fastapi.testclient import TestClient

    from packages.auth.audit_middleware import AuditMiddleware

    def failing_writer(_event: dict[str, object]) -> None:
        raise RuntimeError("database unavailable")

    app = FastAPI()
    app.add_middleware(AuditMiddleware, audit_writer=failing_writer)

    @app.post("/api/strategies")
    def reject_strategy() -> JSONResponse:
        return JSONResponse({"error": "auth_required"}, status_code=401)

    response = TestClient(app).post("/api/strategies")

    assert response.status_code == 401
