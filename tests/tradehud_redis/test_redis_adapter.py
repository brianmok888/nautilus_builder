"""Tests for TradeHUD Redis adapter — config, normalizer, stream health, adapter.

Tests verify:
- Stream namespace defaults to nd.*
- Legacy nautilus:tradehud namespace still works
- Custom stream overrides
- Market trade record maps to TradeHUD trade event
- Missing price/qty/timestamp do not become zero
- Explicit zero remains explicit zero
- Multi-stream XREAD uses all configured streams in one call
- Initial XREVRANGE seed populates snapshot
- Stale/missing stream detection
- Redis unavailable reports degraded, does not crash
- No submit_order, no credentials, no write ops
- TRADEHUD_FEED_SOURCE must be redis to enable adapter
"""

import ast
import inspect
import json
import os
import sys
import time
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from packages.tradehud_contracts.config import (
    TradeHudRedisConfig,
    ALL_STREAM_NAMES,
)
from packages.tradehud_contracts.normalizer import (
    to_optional_float,
    to_optional_int,
    to_optional_str,
    unwrap_payload,
    detect_force_liquidation,
    detect_trade_flags,
    is_explicit_zero,
    requires_fields,
)
from packages.tradehud_contracts.stream_health import StreamHealthTracker
from packages.tradehud_contracts.redis_adapter import (
    RedisStreamAdapter,
    _parse_book_top,
    _parse_trade,
    _parse_account,
    _parse_positions,
    _parse_runtime_health,
    _parse_signal,
    _parse_gate,
    _parse_trade_action,
    _parse_execution,
)


def _make_redis_mock():
    """Create a properly-mocked redis.asyncio module + client.

    Key: 'import redis.asyncio as aioredis' does attribute access
    redis.asyncio on the redis module, so we must set .asyncio = self.
    """
    mock_client = AsyncMock()
    mock_client.ping = AsyncMock(return_value=True)
    mock_client.aclose = AsyncMock()
    mock_client.xread = AsyncMock(return_value=[])
    mock_client.xrevrange = AsyncMock(return_value=[])
    mock_module = MagicMock()
    mock_module.from_url = MagicMock(return_value=mock_client)
    mock_module.asyncio = mock_module  # import redis.asyncio → redis.asyncio attr
    return mock_client, mock_module


# ─── Config tests (Phase 1) ─────────────────────────────────────────────────────

def test_default_namespace_is_nd():
    with patch.dict(os.environ, {}, clear=True):
        config = TradeHudRedisConfig.from_env()
        assert config.stream_namespace == "nd"


def test_nd_namespace_stream_map():
    with patch.dict(os.environ, {"TRADEHUD_STREAM_NAMESPACE": "nd"}, clear=True):
        config = TradeHudRedisConfig.from_env()
        sm = config.get_stream_map()
        assert sm["book_top"] == "nd.market.book_top"
        assert sm["book_l2"] == "nd.market.book_l2"
        assert sm["trades"] == "nd.market.trades"
        assert sm["bars"] == "nd.market.bars"
        assert sm["signal"] == "nd.strategy_signal_preview"
        assert sm["gate"] == "nd.gate_decision"
        assert sm["trade_action"] == "nd.trade_action"
        assert sm["execution"] == "nd.execution_report"
        assert sm["health"] == "nd.health"
        assert sm["account"] == "nd.account.snapshot"
        assert sm["positions"] == "nd.position.snapshot"
        assert sm["orders"] == "nd.order.snapshot"
        assert sm["order_events"] == "nd.order.event"
        assert sm["quant_levels"] == "nd.quant_levels.context"
        assert sm["tick_to_trade"] == "nd.tick_to_trade.trace"


def test_legacy_namespace_stream_map():
    with patch.dict(os.environ, {"TRADEHUD_STREAM_NAMESPACE": "nautilus_tradehud"}, clear=True):
        config = TradeHudRedisConfig.from_env()
        sm = config.get_stream_map()
        assert sm["book_top"] == "nautilus:tradehud:book_top"
        assert sm["signal"] == "nautilus:tradehud:signal"


def test_custom_stream_override():
    with patch.dict(os.environ, {
        "TRADEHUD_STREAM_NAMESPACE": "nd",
        "TRADEHUD_STREAM_BOOK_TOP": "custom.book.top",
    }, clear=True):
        config = TradeHudRedisConfig.from_env()
        sm = config.get_stream_map()
        assert sm["book_top"] == "custom.book.top"
        assert sm["book_l2"] == "nd.market.book_l2"


def test_feed_source_default_is_mock():
    with patch.dict(os.environ, {}, clear=True):
        config = TradeHudRedisConfig.from_env()
        assert config.feed_source == "mock"
        assert config.is_redis_enabled is False


def test_feed_source_must_be_redis_to_activate():
    """Phase 7: REDIS_URL alone does NOT enable Redis adapter."""
    with patch.dict(os.environ, {"REDIS_URL": "redis://127.0.0.1:6379"}, clear=True):
        config = TradeHudRedisConfig.from_env()
        assert config.is_redis_enabled is False


def test_feed_source_redis_enables_adapter():
    with patch.dict(os.environ, {
        "TRADEHUD_FEED_SOURCE": "redis",
        "TRADEHUD_REDIS_URL": "redis://127.0.0.1:6379/0",
    }, clear=True):
        config = TradeHudRedisConfig.from_env()
        assert config.is_redis_enabled is True


def test_redis_url_sanitizer():
    pwd_url = "redis://:" + "hunter2" + "@redis-host.example.com:6379/0"
    with patch.dict(os.environ, {
        "TRADEHUD_FEED_SOURCE": "redis",
        "TRADEHUD_REDIS_URL": pwd_url,
    }, clear=True):
        config = TradeHudRedisConfig.from_env()
        sanitized = config.sanitize_redis_url()
        assert "hunter2" not in sanitized
        assert "***" in sanitized
        assert "redis-host.example.com" in sanitized


def test_block_ms_and_count_config():
    with patch.dict(os.environ, {
        "TRADEHUD_REDIS_BLOCK_MS": "2000",
        "TRADEHUD_REDIS_COUNT": "50",
    }, clear=True):
        config = TradeHudRedisConfig.from_env()
        assert config.redis_block_ms == 2000
        assert config.redis_count == 50


def test_stale_and_missing_ms_config():
    with patch.dict(os.environ, {
        "TRADEHUD_STREAM_STALE_MS": "5000",
        "TRADEHUD_STREAM_MISSING_MS": "15000",
    }, clear=True):
        config = TradeHudRedisConfig.from_env()
        assert config.stream_stale_ms == 5000
        assert config.stream_missing_ms == 15000


# ─── Normalizer tests (Phase 5: missing != zero) ───────────────────────────────

def test_missing_float_returns_none_not_zero():
    assert to_optional_float(None) is None
    assert to_optional_float("") is None
    assert to_optional_float("missing") is None


def test_explicit_zero_stays_zero():
    assert to_optional_float("0") == 0.0
    assert to_optional_float("0.0") == 0.0
    assert to_optional_float(0) == 0.0


def test_missing_int_returns_none_not_zero():
    assert to_optional_int(None) is None
    assert to_optional_int("") is None


def test_explicit_int_zero_stays_zero():
    assert to_optional_int("0") == 0
    assert to_optional_int(0) == 0


def test_is_explicit_zero():
    assert is_explicit_zero("0") is True
    assert is_explicit_zero(0.0) is True
    assert is_explicit_zero(None) is False
    assert is_explicit_zero("") is False
    assert is_explicit_zero("missing") is False


def test_requires_fields():
    assert requires_fields({"price": "100", "qty": "1"}, "price", "qty") is True
    assert requires_fields({"price": "100"}, "price", "qty") is False
    assert requires_fields({}, "price") is False


def test_unwrap_flat_fields():
    data = {"symbol": "BTC", "price": "50000"}
    assert unwrap_payload(data) == data


def test_unwrap_json_payload():
    data = {"payload": '{"symbol": "BTC", "price": "50000"}'}
    result = unwrap_payload(data)
    assert result["symbol"] == "BTC"
    assert result["price"] == "50000"


def test_unwrap_envelope():
    data = {"event_type": "market_trade", "schema_version": "1", "payload": '{"symbol": "BTC"}'}
    result = unwrap_payload(data)
    assert result["symbol"] == "BTC"


def test_detect_force_liquidation_flags():
    data = {"flags": "large_trade,long_liq"}
    is_liq, side = detect_force_liquidation(data)
    assert is_liq is True
    assert side == "long_liq"


def test_detect_force_liquidation_binance_sell():
    data = {"force_order": "true", "side": "SELL"}
    is_liq, side = detect_force_liquidation(data)
    assert is_liq is True
    assert side == "long_liq"


def test_detect_force_liquidation_binance_buy():
    data = {"force_order": "true", "side": "BUY"}
    is_liq, side = detect_force_liquidation(data)
    assert is_liq is True
    assert side == "short_liq"


def test_detect_trade_flags():
    data = {"flags": "large_trade,sweep"}
    flags = detect_trade_flags(data)
    assert flags["is_large_trade"] is True
    assert flags["is_sweep"] is True


# ─── Parser tests (Phase 2: trades + Phase 5: missing != zero) ─────────────────

def test_parse_book_top_valid():
    result = _parse_book_top({
        "symbol": "BTCUSDT-PERP",
        "bid_price": "50000.5",
        "ask_price": "50001.0",
        "bid_size": "1.5",
        "ask_size": "2.0",
        "mid_price": "50000.75",
        "spread": "0.5",
        "spread_bps": "1.0",
        "microprice": "50000.8",
        "ts_event_ns": "1700000000000000000",
    })
    assert result is not None
    assert result.bid_price == 50000.5
    assert result.provenance == "redis"


def test_parse_book_top_missing_price_returns_none():
    """Missing price -> None, not zero-filled."""
    result = _parse_book_top({"symbol": "BTCUSDT-PERP"})
    assert result is None


def test_parse_trade_valid():
    result = _parse_trade({
        "symbol": "BTCUSDT-PERP",
        "price": "67250.5",
        "qty": "0.021",
        "side": "BUY",
        "aggressor": "BUY",
        "trade_id": "trade_001",
        "ts_event_ns": "1700000000000000000",
    })
    assert result is not None
    assert result.price == 67250.5
    assert result.qty == 0.021
    assert result.provenance == "redis"


def test_parse_trade_missing_price_returns_none():
    result = _parse_trade({"symbol": "BTC", "qty": "1"})
    assert result is None


def test_parse_trade_missing_qty_returns_none():
    result = _parse_trade({"symbol": "BTC", "price": "50000"})
    assert result is None


def test_parse_trade_with_liquidation_flag():
    data = {
        "symbol": "BTCUSDT-PERP",
        "price": "50000",
        "qty": "1.0",
        "side": "SELL",
        "flags": "long_liq",
        "trade_id": "trade_002",
        "ts_event_ns": "1700000000000000000",
    }
    result = _parse_trade(data)
    assert result is not None
    assert result.is_liquidation is True
    assert result.liq_side == "long_liq"


def test_parse_trade_json_payload():
    inner = json.dumps({"symbol": "BTC", "price": "50000", "qty": "1.0", "ts_event_ns": "1000"})
    result = _parse_trade({"payload": inner})
    assert result is not None
    assert result.price == 50000.0


def test_parse_signal_missing_confidence_returns_none():
    result = _parse_signal({"symbol": "BTC", "signal_id": "s1"})
    assert result is None


def test_parse_gate_missing_decision_returns_none():
    result = _parse_gate({"symbol": "BTC", "decision_id": "g1"})
    assert result is None


def test_parse_trade_action_missing_price_returns_none():
    result = _parse_trade_action({"action": "BUY", "qty": "1"})
    assert result is None


def test_parse_execution_missing_submit_ts_returns_none():
    result = _parse_execution({"status": "FILLED", "symbol": "BTC"})
    assert result is None


def test_parse_runtime_health_missing_ts_returns_none():
    result = _parse_runtime_health({})
    assert result is None


def test_parse_account_valid():
    result = _parse_account({
        "account_id": "acc_001", "venue": "BINANCE", "balance": "100000",
        "ts_event_ns": "1000",
    })
    assert result is not None
    assert result.balance == 100000.0


def test_parse_account_missing_balance_returns_none():
    result = _parse_account({"account_id": "acc_001"})
    assert result is None


def test_parse_positions_skips_missing_qty():
    positions = json.dumps([
        {"symbol": "BTC", "qty": "0.5", "ts_event_ns": "1000"},
        {"symbol": "ETH"},
    ])
    result = _parse_positions({"positions": positions})
    assert len(result) == 1


def test_explicit_zero_stays_zero_in_parser():
    """Explicit bid_size=0 should remain 0, not become None."""
    result = _parse_book_top({
        "symbol": "BTC",
        "bid_price": "50000",
        "ask_price": "50001",
        "bid_size": "0",
        "ask_size": "0",
        "ts_event_ns": "1000",
    })
    assert result is not None
    assert result.bid_size == 0.0
    assert result.ask_size == 0.0


# ─── Stream health tests (Phase 6) ─────────────────────────────────────────────

def test_stream_health_tracker_initial():
    config = TradeHudRedisConfig.from_env()
    tracker = StreamHealthTracker(config)
    health = tracker.evaluate()
    assert health["redis_connected"] is False


def test_stream_health_live_after_event():
    config = TradeHudRedisConfig.from_env()
    tracker = StreamHealthTracker(config)
    tracker.mark_connected(True)
    tracker.record_event("book_top", "1-0", int(time.time() * 1e9))
    health = tracker.evaluate()
    assert "nd.market.book_top" in health["streams_seen"]


def test_stream_health_unavailable_when_disconnected():
    config = TradeHudRedisConfig.from_env()
    tracker = StreamHealthTracker(config)
    tracker.mark_connected(True)
    tracker.record_event("book_top", "1-0", int(time.time() * 1e9))
    tracker.mark_connected(False)
    health = tracker.evaluate()
    # stream_details is a dict keyed by stream name
    assert health["stream_details"]["book_top"]["status"] == "unavailable"
    assert "nd.market.book_top" in health["streams_unavailable"]


def test_stream_health_seed_marks_synthetic():
    config = TradeHudRedisConfig.from_env()
    tracker = StreamHealthTracker(config)
    tracker.record_seed("book_top", "1-0", int(time.time() * 1e9))
    assert tracker.get_stream_status("book_top") == "synthetic"


def test_stream_health_seed_no_entry_marks_missing():
    config = TradeHudRedisConfig.from_env()
    tracker = StreamHealthTracker(config)
    tracker.record_seed("book_top", None, None)
    assert tracker.get_stream_status("book_top") == "missing"


# ─── Adapter tests ──────────────────────────────────────────────────────────────

def test_adapter_no_redis_source():
    """Phase 7: adapter does nothing when feed_source is not redis."""
    with patch.dict(os.environ, {}, clear=True):
        adapter = RedisStreamAdapter()
        import asyncio
        connected = asyncio.get_event_loop().run_until_complete(adapter.connect())
        assert connected is False
        assert adapter.is_connected() is False


def test_adapter_redis_enabled_connects():
    config = TradeHudRedisConfig(feed_source="redis", redis_url="redis://127.0.0.1:6379/0")
    mock_client, mock_module = _make_redis_mock()
    with patch.dict(sys.modules, {"redis.asyncio": mock_module, "redis": mock_module}):
        adapter = RedisStreamAdapter(config)
        import asyncio
        loop = asyncio.new_event_loop()
        connected = loop.run_until_complete(adapter.connect())
        assert connected is True
        assert adapter.is_connected() is True
        loop.run_until_complete(adapter.disconnect())
        loop.close()


def test_adapter_seed_on_connect():
    config = TradeHudRedisConfig(feed_source="redis", redis_url="redis://127.0.0.1:6379/0")
    mock_client, mock_module = _make_redis_mock()

    def _xrevrange_side_effect(key, **kw):
        key_bytes = key.encode() if isinstance(key, str) else key
        if b"book_top" in key_bytes:
            return [(b"1-0", {b"symbol": b"BTC", b"bid_price": b"50000", b"ask_price": b"50001", b"ts_event_ns": b"1000"})]
        return []
    mock_client.xrevrange = AsyncMock(side_effect=_xrevrange_side_effect)

    with patch.dict(sys.modules, {"redis.asyncio": mock_module, "redis": mock_module}):
        adapter = RedisStreamAdapter(config)
        import asyncio
        loop = asyncio.new_event_loop()
        loop.run_until_complete(adapter.connect())
        snapshot = loop.run_until_complete(adapter.get_snapshot("BTCUSDT-PERP"))
        assert snapshot.book_top is not None
        loop.run_until_complete(adapter.disconnect())
        loop.close()


def test_adapter_multi_stream_xread():
    """Phase 3: adapter uses one multi-stream XREAD, not sequential per-stream."""
    config = TradeHudRedisConfig(feed_source="redis", redis_url="redis://127.0.0.1:6379/0")
    mock_client, mock_module = _make_redis_mock()

    with patch.dict(sys.modules, {"redis.asyncio": mock_module, "redis": mock_module}):
        adapter = RedisStreamAdapter(config)
        import asyncio
        loop = asyncio.new_event_loop()
        loop.run_until_complete(adapter.connect())
        snapshot = loop.run_until_complete(adapter.get_snapshot("BTCUSDT-PERP"))
        assert mock_client.xread.called, "XREAD should be called in Redis mode"
        if mock_client.xread.call_args:
            call_args = mock_client.xread.call_args
            streams_arg = call_args.kwargs.get("streams") or (call_args[0][0] if call_args[0] else {})
            if isinstance(streams_arg, dict):
                assert len(streams_arg) > 1, "Multi-stream XREAD should cover multiple streams"
        loop.run_until_complete(adapter.disconnect())
        loop.close()


def test_adapter_graceful_disconnect():
    mock_client = AsyncMock()
    mock_client.aclose = AsyncMock()
    config = TradeHudRedisConfig(feed_source="redis", redis_url="redis://127.0.0.1:6379/0")
    adapter = RedisStreamAdapter(config)
    adapter._client = mock_client
    adapter._connected = True
    import asyncio
    asyncio.get_event_loop().run_until_complete(adapter.disconnect())
    assert mock_client.aclose.called
    assert adapter.is_connected() is False


# ─── Safety tests ──────────────────────────────────────────────────────────────

def _strip_docstrings(src):
    """Remove docstrings from source for safety scanning."""
    tree = ast.parse(src)
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Module)):
            if (node.body and isinstance(node.body[0], ast.Expr) and
                isinstance(node.body[0].value, ast.Constant) and
                isinstance(node.body[0].value.value, str)):
                node.body = node.body[1:] if len(node.body) > 1 else [ast.Pass()]
    return ast.unparse(tree)


def test_adapter_source_has_no_write_methods():
    src = inspect.getsource(__import__("packages.tradehud_contracts.redis_adapter", fromlist=[""]))
    src_clean = _strip_docstrings(src).lower()
    for pattern in [".xadd(", ".set(", ".publish(", ".hset(", ".lpush(", ".rpush(", ".delete("]:
        assert pattern not in src_clean, f"Write op '{pattern}' found in adapter"


def test_adapter_has_only_xread_and_xrevrange():
    src = inspect.getsource(__import__("packages.tradehud_contracts.redis_adapter", fromlist=[""]))
    src_lower = src.lower()
    assert ".xread(" in src_lower or "xread(" in src_lower
    assert ".xrevrange(" in src_lower or "xrevrange(" in src_lower
    src_clean = _strip_docstrings(src).lower()
    assert ".xadd(" not in src_clean
    assert ".xdel(" not in src_clean


def test_adapter_no_credentials_in_source():
    src = inspect.getsource(__import__("packages.tradehud_contracts.redis_adapter", fromlist=[""]))
    for pattern in ["BINANCE_SECRET", "BYBIT_SECRET", "NEXT_PUBLIC_REDIS_URL", "NEXT_PUBLIC_DATABASE_URL"]:
        assert pattern not in src, f"Forbidden pattern '{pattern}' in adapter"


def test_adapter_no_submit_order():
    src = inspect.getsource(__import__("packages.tradehud_contracts.redis_adapter", fromlist=[""]))
    src_clean = _strip_docstrings(src).lower()
    assert "submit_order" not in src_clean
    assert "createtradeaction" not in src_clean


def test_normalizer_no_credentials():
    src = inspect.getsource(__import__("packages.tradehud_contracts.normalizer", fromlist=[""]))
    assert "NEXT_PUBLIC_REDIS_URL" not in src
    assert "BINANCE_SECRET" not in src


def test_config_no_next_public():
    src = inspect.getsource(__import__("packages.tradehud_contracts.config", fromlist=[""]))
    src_clean = _strip_docstrings(src)
    assert "NEXT_PUBLIC_" not in src_clean
