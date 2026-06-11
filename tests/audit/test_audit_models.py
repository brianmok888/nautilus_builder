"""Tests for audit event model."""
from __future__ import annotations

from packages.audit.models import AuditEvent, REQUIRED_AUDIT_EVENTS


class TestAuditEvent:
    def test_audit_event_creation(self):
        event = AuditEvent(
            audit_event_id="ae_001",
            event_type="strategy.created",
            actor_id="user_001",
            tenant_id="tenant_001",
            request_id="req_001",
            entity_type="strategy",
            entity_id="strat_001",
        )
        assert event.audit_event_id == "ae_001"
        assert event.event_type == "strategy.created"
        assert event.actor_id == "user_001"
        assert event.created_at_utc != ""

    def test_audit_event_with_hashes(self):
        event = AuditEvent(
            audit_event_id="ae_002",
            event_type="strategy.updated",
            before_hash="a" * 64,
            after_hash="b" * 64,
        )
        assert event.before_hash == "a" * 64
        assert event.after_hash == "b" * 64

    def test_audit_event_extra_fields_forbidden(self):
        import pytest
        with pytest.raises(Exception):
            AuditEvent(
                audit_event_id="ae_003",
                event_type="test",
                unknown="bad",
            )

    def test_required_audit_events_cover_spec(self):
        expected = {
            "strategy.created", "strategy.updated", "strategy.validated",
            "strategy.compiled", "backtest.started", "backtest.completed",
            "evidence.created", "evidence.verified",
            "promotion.requested", "promotion.blocked", "promotion.approved",
            "readiness.checked", "config.changed",
        }
        assert expected.issubset(REQUIRED_AUDIT_EVENTS)

    def test_no_live_execution_events(self):
        """Builder audit must not have live execution/order events."""
        for event_type in REQUIRED_AUDIT_EVENTS:
            assert "live_execution" not in event_type
            assert "submit_order" not in event_type
            assert "trade_action" not in event_type
