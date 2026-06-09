"""Tests for audit middleware and request ID middleware.

TDD RED phase: these tests define expected behavior before implementation.
"""
from __future__ import annotations

from unittest.mock import MagicMock



class TestAuditMiddleware:
    """AuditMiddleware logs mutation requests to audit store."""

    def _make_app(self, audit_writer=None):
        """Create a minimal FastAPI app with audit middleware for testing."""
        from fastapi import FastAPI
        from packages.auth.audit_middleware import AuditMiddleware

        app = FastAPI()

        if audit_writer is None:
            audit_writer = MagicMock()

        app.add_middleware(AuditMiddleware, audit_writer=audit_writer)

        @app.get("/api/test")
        def get_handler():
            return {"status": "ok"}

        @app.post("/api/test")
        def post_handler():
            return {"status": "created"}

        @app.put("/api/test/{item_id}")
        def put_handler(item_id: str):
            return {"status": "updated", "id": item_id}

        @app.delete("/api/test/{item_id}")
        def delete_handler(item_id: str):
            return {"status": "deleted", "id": item_id}

        @app.get("/health/live")
        def health_handler():
            return {"status": "alive"}

        return app

    def test_import_exists(self):
        from packages.auth.audit_middleware import AuditMiddleware
        assert AuditMiddleware is not None

    def test_post_mutation_creates_audit_event(self):
        """POST requests create an audit event."""
        from fastapi.testclient import TestClient

        audit_writer = MagicMock()
        app = self._make_app(audit_writer=audit_writer)
        client = TestClient(app)

        response = client.post("/api/test")
        assert response.status_code == 200
        audit_writer.assert_called_once()

    def test_put_mutation_creates_audit_event(self):
        """PUT requests create an audit event."""
        from fastapi.testclient import TestClient

        audit_writer = MagicMock()
        app = self._make_app(audit_writer=audit_writer)
        client = TestClient(app)

        response = client.put("/api/test/123")
        assert response.status_code == 200
        audit_writer.assert_called_once()

    def test_delete_mutation_creates_audit_event(self):
        """DELETE requests create an audit event."""
        from fastapi.testclient import TestClient

        audit_writer = MagicMock()
        app = self._make_app(audit_writer=audit_writer)
        client = TestClient(app)

        response = client.delete("/api/test/123")
        assert response.status_code == 200
        audit_writer.assert_called_once()

    def test_get_does_not_create_audit_event(self):
        """GET requests do NOT create audit events."""
        from fastapi.testclient import TestClient

        audit_writer = MagicMock()
        app = self._make_app(audit_writer=audit_writer)
        client = TestClient(app)

        response = client.get("/api/test")
        assert response.status_code == 200
        audit_writer.assert_not_called()

    def test_health_endpoint_no_audit_event(self):
        """Health endpoints do NOT create audit events."""
        from fastapi.testclient import TestClient

        audit_writer = MagicMock()
        app = self._make_app(audit_writer=audit_writer)
        client = TestClient(app)

        response = client.get("/health/live")
        assert response.status_code == 200
        audit_writer.assert_not_called()

    def test_audit_event_contains_required_fields(self):
        """Audit event dict has all required fields."""
        from fastapi.testclient import TestClient

        audit_writer = MagicMock()
        app = self._make_app(audit_writer=audit_writer)
        client = TestClient(app)

        response = client.post("/api/test")
        assert response.status_code == 200

        call_args = audit_writer.call_args
        event = call_args[0][0]  # First positional argument

        required_fields = {"request_id", "route", "method", "status_code", "created_at"}
        assert required_fields.issubset(set(event.keys()))

    def test_audit_event_method_is_post(self):
        """Audit event records correct HTTP method."""
        from fastapi.testclient import TestClient

        audit_writer = MagicMock()
        app = self._make_app(audit_writer=audit_writer)
        client = TestClient(app)

        client.post("/api/test")
        event = audit_writer.call_args[0][0]
        assert event["method"] == "POST"

    def test_audit_writer_failure_returns_deterministic_error(self):
        from fastapi.testclient import TestClient

        def broken_audit_writer(event: dict) -> None:
            raise RuntimeError("database unavailable")

        app = self._make_app(audit_writer=broken_audit_writer)
        client = TestClient(app)

        response = client.post("/api/test")

        assert response.status_code == 500
        assert response.json()["error"] == "audit_write_failed"


class TestRequestIdMiddleware:
    """Request ID middleware adds X-Request-ID to all responses."""

    def _make_app(self):
        from fastapi import FastAPI
        from packages.auth.audit_middleware import RequestIdMiddleware

        app = FastAPI()
        app.add_middleware(RequestIdMiddleware)

        @app.get("/api/test")
        def handler():
            return {"status": "ok"}

        return app

    def test_import_exists(self):
        from packages.auth.audit_middleware import RequestIdMiddleware
        assert RequestIdMiddleware is not None

    def test_response_has_request_id_header(self):
        """Responses include X-Request-ID header."""
        from fastapi.testclient import TestClient

        app = self._make_app()
        client = TestClient(app)

        response = client.get("/api/test")
        assert "x-request-id" in response.headers

    def test_request_id_is_uuid_format(self):
        """X-Request-ID is a valid UUID."""
        import uuid
        from fastapi.testclient import TestClient

        app = self._make_app()
        client = TestClient(app)

        response = client.get("/api/test")
        request_id = response.headers["x-request-id"]
        # Should not raise
        uuid.UUID(request_id)

    def test_request_id_unique_per_request(self):
        """Each request gets a unique request ID."""
        from fastapi.testclient import TestClient

        app = self._make_app()
        client = TestClient(app)

        ids = set()
        for _ in range(5):
            response = client.get("/api/test")
            ids.add(response.headers["x-request-id"])

        assert len(ids) == 5

    def test_incoming_request_id_preserved(self):
        """If client sends X-Request-ID, it is preserved."""
        from fastapi.testclient import TestClient

        app = self._make_app()
        client = TestClient(app)

        response = client.get("/api/test", headers={"X-Request-ID": "custom-id-123"})
        assert response.headers["x-request-id"] == "custom-id-123"
