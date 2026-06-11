"""Tests for auth capabilities model."""
from __future__ import annotations

from packages.auth.capabilities import (
    Capability,
    DEFAULT_OPERATOR_CAPABILITIES,
    ADMIN_CAPABILITIES,
    has_capability,
)


class TestCapabilities:
    def test_all_capabilities_have_scope_format(self):
        for cap in Capability:
            assert ":" in cap.value

    def test_operator_has_read_write_run(self):
        assert Capability.STRATEGY_READ in DEFAULT_OPERATOR_CAPABILITIES
        assert Capability.STRATEGY_WRITE in DEFAULT_OPERATOR_CAPABILITIES
        assert Capability.BACKTEST_RUN in DEFAULT_OPERATOR_CAPABILITIES

    def test_operator_cannot_approve_promotion(self):
        assert Capability.PROMOTION_APPROVE not in DEFAULT_OPERATOR_CAPABILITIES

    def test_admin_has_all_capabilities(self):
        assert ADMIN_CAPABILITIES == set(Capability)

    def test_has_capability_check(self):
        assert has_capability(DEFAULT_OPERATOR_CAPABILITIES, Capability.STRATEGY_READ)
        assert not has_capability(DEFAULT_OPERATOR_CAPABILITIES, Capability.PROMOTION_APPROVE)

    def test_no_live_execution_capability(self):
        """Builder must never have a live execution capability."""
        for cap in Capability:
            assert "live" not in cap.value.lower() or cap.value == ""
            assert "submit_order" not in cap.value.lower()
            assert "trade_action" not in cap.value.lower()
