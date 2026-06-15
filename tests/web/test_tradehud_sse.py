"""Tests for TradeHUD SSE event stream generator.

Verifies the SSE stream produces correctly formatted events,
is read-only, and contains no credentials or order authority.
"""

import asyncio
import json
import pytest
from services.api.routes.tradehud_sse import (
    tradehud_event_stream,
    _format_sse,
    _format_ping,
)


class TestSSEFormat:
    def test_format_sse_produces_valid_sse(self):
        data = {"price": 50000, "symbol": "BTCUSDT-PERP"}
        result = _format_sse("BOOK_TOP", data)
        assert result.startswith(b"data: ")
        assert result.endswith(b"\n\n")
        parsed = json.loads(result[6:-2])
        assert parsed["type"] == "BOOK_TOP"
        assert parsed["payload"]["price"] == 50000

    def test_format_ping(self):
        result = _format_ping()
        assert result == b": ping\n\n"


class TestSSEStream:
    @pytest.mark.asyncio
    async def test_stream_produces_initial_snapshot(self):
        """Stream should emit initial snapshot events immediately."""
        events = []
        gen = tradehud_event_stream("BTCUSDT-PERP")

        # Collect first few events (initial snapshot burst)
        try:
            for _ in range(5):
                event = await asyncio.wait_for(gen.__anext__(), timeout=2.0)
                events.append(event)
        except (asyncio.TimeoutError, StopAsyncIteration):
            pass
        finally:
            await gen.aclose()

        assert len(events) > 0
        # First event should be BOOK_TOP or BOOK_L2
        first = json.loads(events[0][6:-2])
        assert first["type"] in ("BOOK_TOP", "BOOK_L2", "ACCOUNT", "QUANT_LEVELS", "RUNTIME_HEALTH")

    @pytest.mark.asyncio
    async def test_stream_events_are_valid_json(self):
        """All data: events must be valid JSON with type and payload."""
        gen = tradehud_event_stream("BTCUSDT-PERP")
        try:
            for _ in range(6):
                event = await asyncio.wait_for(gen.__anext__(), timeout=2.0)
                if event.startswith(b": "):
                    continue  # ping
                assert event.startswith(b"data: ")
                payload_str = event[6:].strip()
                parsed = json.loads(payload_str)
                assert "type" in parsed
                assert "payload" in parsed
        except (asyncio.TimeoutError, StopAsyncIteration):
            pass
        finally:
            await gen.aclose()

    @pytest.mark.asyncio
    async def test_stream_contains_no_credentials(self):
        """SSE stream must not expose any credentials."""
        gen = tradehud_event_stream("BTCUSDT-PERP")
        collected = b""
        try:
            for _ in range(10):
                event = await asyncio.wait_for(gen.__anext__(), timeout=2.0)
                collected += event.lower()
        except (asyncio.TimeoutError, StopAsyncIteration):
            pass
        finally:
            await gen.aclose()

        collected_str = collected.decode("utf-8", errors="replace")
        for forbidden in [
            "api_key", "secret_key", "private_key",
            "binance_secret", "bybit_secret", "okx_secret",
            "password", "token",
        ]:
            assert forbidden not in collected_str, f"Found {forbidden} in SSE stream"

    @pytest.mark.asyncio
    async def test_stream_contains_no_order_authority(self):
        """SSE stream must not contain submit_order or create_trade_action calls."""
        gen = tradehud_event_stream("BTCUSDT-PERP")
        collected = b""
        try:
            for _ in range(10):
                event = await asyncio.wait_for(gen.__anext__(), timeout=2.0)
                collected += event
        except (asyncio.TimeoutError, StopAsyncIteration):
            pass
        finally:
            await gen.aclose()

        collected_str = collected.decode("utf-8", errors="replace").lower()
        for forbidden in [
            "submit_order(", "create_trade_action(",
            "force_approve(",
        ]:
            assert forbidden not in collected_str, f"Found {forbidden} in SSE stream"

    @pytest.mark.asyncio
    async def test_stream_is_cancellable(self):
        """Stream should clean up when cancelled."""
        gen = tradehud_event_stream("BTCUSDT-PERP")
        # Read one event
        await gen.__anext__()
        # Cancel — should not raise
        await gen.aclose()
