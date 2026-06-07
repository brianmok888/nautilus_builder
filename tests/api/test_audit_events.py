"""Tests for audit event logging model."""
from __future__ import annotations

import pytest

from packages.runtime_events.models import AuditEvent, audit_event_from_mutation


class TestAuditEvent:
    def test_audit_event_creation(self):
        event = AuditEvent(
            request_id="req-001",
            actor_id="user-001",
            action="strategy.create",
            resource_type="strategy",
            resource_id="strat-001",
            status="success",
        )
        assert event.request_id == "req-001"
        assert event.action == "strategy.create"
        assert event.status == "success"

    def test_audit_event_with_hashes(self):
        event = AuditEvent(
            request_id="req-002",
            actor_id="user-001",
            action="strategy.update",
            resource_type="strategy",
            resource_id="strat-002",
            before_hash="hash_before",
            after_hash="hash_after",
            status="success",
        )
        assert event.before_hash == "hash_before"
        assert event.after_hash == "hash_after"

    def test_audit_event_with_error(self):
        event = AuditEvent(
            request_id="req-003",
            actor_id="user-001",
            action="promotion.request",
            resource_type="promotion",
            resource_id="promo-001",
            status="failed",
            error_code="PROMOTION_BLOCKED",
        )
        assert event.error_code == "PROMOTION_BLOCKED"

    def test_audit_event_from_mutation_helper(self):
        event = audit_event_from_mutation(
            request_id="req-004",
            actor_id="user-002",
            action="compile",
            resource_type="strategy",
            resource_id="strat-003",
            after_hash="hash_new",
        )
        assert event.action == "compile"
        assert event.after_hash == "hash_new"
        assert event.before_hash is None

    def test_audit_event_is_immutable(self):
        event = AuditEvent(
            request_id="req-005",
            actor_id="user-001",
            action="strategy.create",
            resource_type="strategy",
            resource_id="strat-001",
            status="success",
        )
        with pytest.raises(Exception):
            event.action = "strategy.delete"
