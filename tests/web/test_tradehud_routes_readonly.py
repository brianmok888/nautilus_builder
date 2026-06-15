"""Phase 8: Backend read-only route verification for TradeHUD.

Confirms all TradeHUD endpoints are GET-only, return synthetic provenance,
and expose no credentials or order-execution authority.
"""

import pytest
import inspect
from services.api.routes.tradehud import (
    tradehud_snapshot_payload,
    tradehud_health_payload,
    tradehud_replay_payload,
)


class TestReadOnlyRoutes:
    """All TradeHUD endpoints must be read-only GET."""

    def test_snapshot_returns_synthetic_provenance(self):
        result = tradehud_snapshot_payload()
        assert result["provenance"] == "mock"

    def test_snapshot_has_no_credentials(self):
        result = tradehud_snapshot_payload()
        result_str = str(result).lower()
        for secret_term in [
            "api_key", "secret_key", "private_key",
            "binance_secret", "bybit_secret", "okx_secret",
            "password", "token",
        ]:
            assert secret_term not in result_str, f"Found {secret_term} in snapshot"

    def test_health_returns_read_only_state(self):
        result = tradehud_health_payload()
        assert result["status"] in ("ok", "degraded", "mock")
        assert result["mode"] in ("mock", "snapshot", "sse")
        assert "observational" in result["message"].lower()
        assert result["has_runtime"] is False
        assert result["has_redis"] is False
        assert result["has_postgres"] is False

    def test_replay_returns_events(self):
        result = tradehud_replay_payload()
        assert "events" in result
        assert isinstance(result["events"], list)
        assert result["provenance"] == "mock"

    def test_no_submit_cancel_modify_in_route_source(self):
        """Route module must not expose submit/cancel/modify endpoints."""
        from services.api.routes import tradehud as mod
        source = inspect.getsource(mod)
        source_lower = source.lower()
        for forbidden in [
            "def submit", "def cancel", "def modify",
            "def approve", "def force_approve",
            "def create_order", "def delete_order",
            "def place_order",
        ]:
            assert forbidden not in source_lower, f"Found {forbidden} in tradehud routes"

    def test_no_post_patch_delete_decorator(self):
        """Route module must not have POST/PATCH/DELETE decorators or registrations."""
        from services.api.routes import tradehud as mod
        source = inspect.getsource(mod)
        source_upper = source.upper()
        for method in ["POST", "PATCH", "DELETE", "PUT"]:
            assert f'"{method}"' not in source_upper, f"Found {method} in tradehud routes"
            assert f"'{method}'" not in source_upper, f"Found {method} in tradehud routes"

    def test_no_redis_import(self):
        """Route module must not import Redis."""
        from services.api.routes import tradehud as mod
        source = inspect.getsource(mod)
        assert "import redis" not in source.lower()
        assert "from redis" not in source.lower()

    def test_no_database_connection(self):
        """Route module must not open database connections."""
        from services.api.routes import tradehud as mod
        source = inspect.getsource(mod)
        source_lower = source.lower()
        assert "psycopg" not in source_lower
        assert "sqlalchemy" not in source_lower
        assert "asyncpg" not in source_lower
