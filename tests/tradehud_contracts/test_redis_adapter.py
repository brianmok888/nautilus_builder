"""Tests for Redis Stream adapter — read-only ND runtime event consumer.

Tests verify:
- Stream entry parsing for all event types
- Snapshot building from collected entries
- Read-only behavior (no XADD, no writes)
- Graceful fallback when Redis unavailable
- No credential exposure
- Provenance markers (redis/live)
"""

import asyncio
import json
import os
import inspect
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from packages.tradehud_contracts.redis_adapter import (
    RedisStreamAdapter,
    parse_stream_entry,
    build_snapshot_from_redis,
    _parse_stream_entry,
    _parse_book_top,
    _parse_account,
    _parse_positions,
    _parse_runtime_health,
    _STREAM_KEYS,
    _STREAM_PREFIX,
)
from packages.tradehud_contracts.models import TradeHudSnapshot


# ─── Stream entry parsing tests ────────────────────────────────────────────────

def test_parse_book_top_from_redis_entry():
    """Book top parsed correctly from Redis stream fields."""
    fields = {
        b"symbol": b"BTCUSDT-PERP",
        b"bid_price": b"50000.5",
        b"ask_price": b"50001.0",
        b"bid_size": b"1.5",
        b"ask_size": b"2.0",
        b"mid_price": b"50000.75",
        b"spread": b"0.5",
        b"spread_bps": b"1.0",
        b"microprice": b"50000.8",
        b"ts_event_ns": b"1700000000000000000",
    }
    result = _parse_book_top(_parse_stream_entry(fields))
    assert result is not None
    assert result.symbol == "BTCUSDT-PERP"
    assert result.bid_price == 50000.5
    assert result.ask_price == 50001.0
    assert result.provenance == "redis"
    assert result.source_status == "live"
    assert result.source_available is True


def test_parse_account_from_redis_entry():
    """Account snapshot parsed correctly from Redis stream fields."""
    fields = {
        b"account_id": b"acc_001",
        b"venue": b"BINANCE-FUTURES",
        b"balance": b"100000.0",
        b"equity": b"105000.0",
        b"available_margin": b"95000.0",
        b"margin_used": b"5000.0",
        b"unrealized_pnl": b"5000.0",
        b"realized_pnl": b"2000.0",
        b"currency": b"USDT",
        b"ts_event_ns": b"1700000000000000000",
    }
    result = _parse_account(_parse_stream_entry(fields))
    assert result is not None
    assert result.account_id == "acc_001"
    assert result.balance == 100000.0
    assert result.provenance == "redis"
    assert result.source_status == "live"


def test_parse_positions_from_redis_entry():
    """Positions parsed from JSON list in Redis stream."""
    fields = {
        b"positions": json.dumps([
            {
                "symbol": "BTCUSDT-PERP",
                "venue": "BINANCE-FUTURES",
                "side": "long",
                "qty": "0.5",
                "entry_price": "49000.0",
                "mark_price": "50000.0",
                "unrealized_pnl": "500.0",
                "realized_pnl": "0.0",
                "margin": "2500.0",
                "ts_event_ns": "1700000000000000000",
            }
        ]).encode(),
    }
    result = _parse_positions(_parse_stream_entry(fields))
    assert len(result) == 1
    assert result[0].symbol == "BTCUSDT-PERP"
    assert result[0].side == "long"
    assert result[0].qty == 0.5
    assert result[0].provenance == "redis"


def test_parse_runtime_health_from_redis_entry():
    """Runtime health parsed with all lanes."""
    fields = {
        b"main_strategy_lane": b"main_strategy",
        b"main_strategy_status": b"healthy",
        b"main_strategy_heartbeat_ns": b"1700000000000000000",
        b"gate_engine_lane": b"gate_engine",
        b"gate_engine_status": b"healthy",
        b"execution_lane_lane": b"execution_lane",
        b"execution_lane_status": b"healthy",
        b"ai_advisory_lane": b"ai_advisory",
        b"ai_advisory_status": b"degraded",
        b"data_lane": b"data",
        b"data_status": b"healthy",
        b"ts_event_ns": b"1700000000000000000",
    }
    result = _parse_runtime_health(_parse_stream_entry(fields))
    assert result is not None
    assert result.run_main_strategy_signal.status == "healthy"
    assert result.run_execution_lane.status == "healthy"
    assert result.ai_lane_advisory.status == "degraded"
    assert result.provenance == "redis"


def test_parse_book_top_missing_fields_returns_none():
    """Missing critical fields → parser returns None, not zero-filled."""
    result = _parse_book_top({"symbol": "BTCUSDT-PERP"})
    assert result is None  # no price fields → not valid book data


def test_parse_stream_entry_unknown_suffix():
    """Unknown stream suffix returns None."""
    result = parse_stream_entry("unknown_stream", {})
    assert result is None


# ─── Snapshot building tests ───────────────────────────────────────────────────

def test_build_snapshot_from_redis_entries():
    """Snapshot built from collected stream entries has redis provenance."""
    entries = {
        "book_top": {
            b"symbol": b"BTCUSDT-PERP",
            b"bid_price": b"50000.0",
            b"ask_price": b"50001.0",
            b"bid_size": b"1.0",
            b"ask_size": b"1.0",
            b"mid_price": b"50000.5",
            b"spread": b"1.0",
            b"spread_bps": b"2.0",
            b"microprice": b"50000.5",
            b"ts_event_ns": b"1700000000000000000",
        },
        "account": {
            b"account_id": b"acc_001",
            b"venue": b"BINANCE-FUTURES",
            b"balance": b"100000.0",
            b"equity": b"105000.0",
            b"available_margin": b"95000.0",
            b"margin_used": b"5000.0",
            b"unrealized_pnl": b"5000.0",
            b"realized_pnl": b"2000.0",
            b"ts_event_ns": b"1700000000000000000",
        },
    }
    snapshot = build_snapshot_from_redis(entries)
    assert snapshot.provenance == "redis"
    assert snapshot.book_top is not None
    assert snapshot.book_top.bid_price == 50000.0
    assert snapshot.account is not None
    assert snapshot.account.balance == 100000.0
    # Missing streams → None, not zero
    assert snapshot.quant_levels is None
    assert snapshot.runtime_health is None


def test_build_snapshot_empty_entries():
    """Empty entries dict → snapshot with all None fields."""
    snapshot = build_snapshot_from_redis({})
    assert snapshot.book_top is None
    assert snapshot.account is None
    assert snapshot.provenance == "redis"  # still marked redis origin


# ─── Adapter behavior tests ────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_adapter_no_redis_url_returns_false():
    """Adapter without REDIS_URL does not connect."""
    with patch.dict(os.environ, {}, clear=True):
        adapter = RedisStreamAdapter()
        connected = await adapter.connect()
        assert connected is False
        assert adapter.is_connected() is False
        assert adapter.is_configured() is False


@pytest.mark.asyncio
async def test_adapter_graceful_connection_failure():
    """Adapter handles connection failure gracefully."""
    adapter = RedisStreamAdapter(redis_url="redis://localhost:6390")  # wrong port
    connected = await adapter.connect()
    assert connected is False
    assert adapter.is_connected() is False
    assert adapter.get_connect_error() is not None


@pytest.mark.asyncio
async def test_adapter_health_when_disconnected():
    """Adapter health shows disconnected when not connected."""
    adapter = RedisStreamAdapter()
    await adapter.connect()
    health = await adapter.get_health()
    assert health["status"] == "disconnected"
    assert health["redis_connected"] is False
    assert health["mode"] == "mock"


@pytest.mark.asyncio
async def test_adapter_get_snapshot_returns_none_when_disconnected():
    """Adapter returns None snapshot when not connected."""
    adapter = RedisStreamAdapter()
    result = await adapter.get_snapshot("BTCUSDT-PERP")
    assert result is None


@pytest.mark.asyncio
async def test_adapter_mock_redis_get_snapshot():
    """Adapter returns snapshot from mock Redis with pre-populated streams."""
    mock_redis = AsyncMock()
    # Simulate XREAD returning entries
    mock_redis.xread.return_value = [
        (
            b"nautilus:tradehud:book_top",
            [(b"1-0", {
                b"symbol": b"BTCUSDT-PERP",
                b"bid_price": b"50000.0",
                b"ask_price": b"50001.0",
                b"bid_size": b"1.0",
                b"ask_size": b"1.0",
                b"mid_price": b"50000.5",
                b"spread": b"1.0",
                b"spread_bps": b"2.0",
                b"microprice": b"50000.5",
                b"ts_event_ns": b"1700000000000000000",
            })],
        ),
    ]
    mock_redis.ping.return_value = True
    mock_redis.aclose = AsyncMock()

    adapter = RedisStreamAdapter(redis_url="redis://localhost:6379")
    adapter._client = mock_redis
    adapter._connected = True

    # First read: gets fresh data
    snapshot = await adapter.get_snapshot("BTCUSDT-PERP")
    assert snapshot is not None
    assert snapshot.provenance == "redis"
    assert snapshot.book_top is not None
    assert snapshot.book_top.bid_price == 50000.0

    # Subsequent read with no new data: falls back to cached
    mock_redis.xread.return_value = []
    snapshot2 = await adapter.get_snapshot("BTCUSDT-PERP")
    assert snapshot2 is not None
    assert snapshot2.book_top is not None  # from cache


@pytest.mark.asyncio
async def test_adapter_disconnect_cleans_up():
    """Disconnect closes client and sets connected=False."""
    mock_redis = AsyncMock()
    mock_redis.aclose = AsyncMock()

    adapter = RedisStreamAdapter(redis_url="redis://localhost:6379")
    adapter._client = mock_redis
    adapter._connected = True

    await adapter.disconnect()
    assert mock_redis.aclose.called
    assert adapter.is_connected() is False
    assert adapter._client is None


# ─── Safety tests ──────────────────────────────────────────────────────────────

def test_adapter_source_has_no_write_methods():
    """Adapter module must not contain write operations (XADD, SET, publish, etc.)."""
    src = inspect.getsource(__import__("packages.tradehud_contracts.redis_adapter", fromlist=[""]))
    forbidden_write_patterns = [
        ".xadd(",
        ".set(",
        ".publish(",
        ".hset(",
        ".lpush(",
        ".rpush(",
        ".sadd(",
        ".zadd(",
        ".setex(",
        ".mset(",
        ".delete(",
    ]
    for pattern in forbidden_write_patterns:
        assert pattern not in src.lower(), f"Write operation '{pattern}' found in redis_adapter.py"


def test_adapter_has_only_xread():
    """Adapter must only use XREAD for Redis operations."""
    src = inspect.getsource(__import__("packages.tradehud_contracts.redis_adapter", fromlist=[""]))
    assert ".xread(" in src.lower(), "Adapter should use XREAD"
    # Ensure no other Redis command methods
    assert ".xadd(" not in src.lower()
    assert ".xdel(" not in src.lower()


def test_adapter_no_credentials_in_source():
    """Adapter source must not contain hardcoded credentials."""
    src = inspect.getsource(__import__("packages.tradehud_contracts.redis_adapter", fromlist=[""]))
    forbidden = [
        "BINANCE_SECRET", "BYBIT_SECRET", "OKX_SECRET", "DERIBIT_SECRET",
        "POLYMARKET_PRIVATE_KEY", "NEXT_PUBLIC_REDIS_URL",
        "NEXT_PUBLIC_DATABASE_URL",
    ]
    for pattern in forbidden:
        assert pattern not in src, f"Forbidden credential pattern '{pattern}' in redis_adapter.py"


def test_adapter_redis_url_not_browser_exposed():
    """Adapter must not reference NEXT_PUBLIC_ env vars."""
    src = inspect.getsource(__import__("packages.tradehud_contracts.redis_adapter", fromlist=[""]))
    assert "NEXT_PUBLIC_" not in src


def test_adapter_no_submit_order():
    """Adapter must not call submit_order or create TradeAction."""
    import ast
    mod = __import__("packages.tradehud_contracts.redis_adapter", fromlist=[""])
    # Get source, strip docstrings/comments
    src = inspect.getsource(mod)
    tree = ast.parse(src)
    # Remove docstrings from AST
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Module)):
            if (node.body and isinstance(node.body[0], ast.Expr) and
                isinstance(node.body[0].value, ast.Constant) and
                isinstance(node.body[0].value.value, str)):
                node.body = node.body[1:] if len(node.body) > 1 else [ast.Pass()]
    src_clean = ast.unparse(tree).lower()
    assert "submit_order" not in src_clean
    assert "createtradeaction" not in src_clean
    assert "create_trade_action" not in src_clean


def test_stream_keys_are_observational_only():
    """All stream keys must be observational (no command/control streams)."""
    forbidden_streams = ["command", "control", "submit", "cancel", "modify", "approve", "force"]
    for key in _STREAM_KEYS:
        for bad in forbidden_streams:
            assert bad not in key.lower(), f"Stream key '{key}' contains forbidden term '{bad}'"


def test_stream_prefix_is_nautilus():
    """Stream prefix must be nautilus:tradehud: (ND convention)."""
    assert _STREAM_PREFIX == "nautilus:tradehud:"
