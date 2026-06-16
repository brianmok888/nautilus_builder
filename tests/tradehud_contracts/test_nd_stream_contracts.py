"""
ND stream name contract tests.

Verifies default namespace, legacy namespace, and custom overrides.
"""
import pytest
from packages.tradehud_contracts.config import TradeHudRedisConfig


class TestNDStreamNamespace:
    def test_default_namespace_is_nd(self):
        c = TradeHudRedisConfig()
        assert c.stream_namespace == "nd"

    def test_nd_stream_map_contains_all_required_streams(self):
        c = TradeHudRedisConfig()
        sm = c.get_stream_map()
        required = {
            "book_top": "nd.public_quote_tick",
            "book_l2": "nd.orderbook_hot_view.tui_state",
            "signal": "nd.strategy_signal_preview",
            "gate": "nd.gate_decision",
            "trade_action": "nd.trade_action",
            "execution": "nd.execution_report",
        }
        for logical, stream_key in required.items():
            assert sm.get(logical) == stream_key, f"{logical} should map to {stream_key}"

    def test_nd_optional_streams_present(self):
        c = TradeHudRedisConfig()
        sm = c.get_stream_map()
        optional = {
            "account": "nd.state_bundle",
            "positions": "nd.state_bundle",
            "tick_to_trade": "nd.latency.tick_to_trade",
        }
        for logical, stream_key in optional.items():
            assert sm.get(logical) == stream_key, f"{logical} should map to {stream_key}"

    def test_get_redis_keys_returns_nd_star(self):
        c = TradeHudRedisConfig()
        keys = c.get_redis_keys()
        assert any(k.startswith("nd.") for k in keys)
        assert "nd.public_quote_tick" in keys
        assert "nd.strategy_signal_preview" in keys


class TestLegacyNamespace:
    def test_legacy_stream_map_resolves(self):
        c = TradeHudRedisConfig(stream_namespace="nautilus_tradehud")
        sm = c.get_stream_map()
        assert sm.get("book_top") == "nautilus:tradehud:book_top"
        assert sm.get("book_top") == "nautilus:tradehud:book_top"
        assert sm.get("health") == "nautilus:tradehud:runtime_health"


class TestCustomOverrides:
    def test_custom_override_takes_precedence(self):
        c = TradeHudRedisConfig(stream_overrides={"book_top": "custom:book_top"})
        sm = c.get_stream_map()
        assert sm["book_top"] == "custom:book_top"

    def test_custom_override_legacy_namespace(self):
        c = TradeHudRedisConfig(
            stream_namespace="nautilus_tradehud",
        )
        sm = c.get_stream_map()
        assert sm["book_top"] == "nautilus:tradehud:book_top"


class TestRedisModeActivation:
    def test_default_is_mock(self):
        c = TradeHudRedisConfig()
        assert c.feed_source == "mock"
        assert not c.is_redis_enabled

    def test_redis_requires_explicit_feed_source(self):
        c = TradeHudRedisConfig(feed_source="mock", redis_url="redis://localhost:6379/0")
        assert not c.is_redis_enabled

    def test_redis_enabled_with_explicit_flag(self):
        c = TradeHudRedisConfig(feed_source="redis", redis_url="redis://localhost:6379/0")
        assert c.is_redis_enabled

    def test_redis_url_alone_does_not_activate(self):
        c = TradeHudRedisConfig(feed_source="mock", redis_url="redis://localhost:6379/0")
        assert not c.is_redis_enabled
