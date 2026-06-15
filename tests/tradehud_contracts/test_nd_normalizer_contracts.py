"""
ND normalizer contract tests.

Verifies missing != true_zero semantics in the normalizer layer.
"""
import json
import pytest
from packages.tradehud_contracts.normalizer import (
    parse_stream_fields,
    to_optional_float,
    to_optional_int,
    to_optional_str,
    is_explicit_zero,
    unwrap_payload,
    detect_force_liquidation,
    detect_trade_flags,
    requires_fields,
)


class TestOptionalParsing:
    def test_none_to_none_float(self):
        assert to_optional_float(None) is None

    def test_empty_string_to_none_float(self):
        assert to_optional_float("") is None

    def test_none_to_none_int(self):
        assert to_optional_int(None) is None

    def test_empty_string_to_none_int(self):
        assert to_optional_int("") is None

    def test_string_zero_is_explicit_zero_float(self):
        assert to_optional_float("0") == 0.0

    def test_string_zero_is_explicit_zero_int(self):
        assert to_optional_int("0") == 0

    def test_float_value_parses(self):
        assert to_optional_float("50000.5") == 50000.5

    def test_int_value_parses(self):
        assert to_optional_int("42") == 42

    def test_invalid_float_returns_none(self):
        assert to_optional_float("abc") is None

    def test_invalid_int_returns_none(self):
        assert to_optional_int("xyz") is None


class TestExplicitZero:
    def test_is_explicit_zero_string_zero(self):
        assert is_explicit_zero("0") is True

    def test_is_explicit_zero_float_zero(self):
        assert is_explicit_zero(0.0) is True

    def test_is_explicit_zero_int_zero(self):
        assert is_explicit_zero(0) is True

    def test_is_explicit_zero_none(self):
        assert is_explicit_zero(None) is False

    def test_is_explicit_zero_empty(self):
        assert is_explicit_zero("") is False

    def test_is_explicit_zero_nonzero(self):
        assert is_explicit_zero("50000") is False

    def test_missing_not_equal_to_zero(self):
        missing = to_optional_float(None)
        zero = to_optional_float("0")
        assert missing is None
        assert zero == 0.0
        assert missing != zero


class TestPayloadUnwrap:
    def test_flat_fields(self):
        data = {"symbol": "BTCUSDT-PERP", "price": "50000"}
        result = unwrap_payload(data)
        assert result["symbol"] == "BTCUSDT-PERP"

    def test_json_payload_envelope(self):
        inner = {"symbol": "BTCUSDT-PERP", "price": "50000"}
        data = {"payload": json.dumps(inner)}
        result = unwrap_payload(data)
        assert result["symbol"] == "BTCUSDT-PERP"

    def test_event_envelope(self):
        inner = {"symbol": "BTCUSDT-PERP", "price": "50000"}
        data = {"event_type": "market_trade", "schema_version": "1", "payload": json.dumps(inner)}
        result = unwrap_payload(data)
        assert result["symbol"] == "BTCUSDT-PERP"

    def test_dict_payload(self):
        data = {"payload": {"symbol": "ETHUSDT-PERP"}}
        result = unwrap_payload(data)
        assert result["symbol"] == "ETHUSDT-PERP"


class TestStreamFieldParsing:
    def test_parse_simple_fields(self):
        fields = {b"symbol": b"BTCUSDT-PERP", b"price": b"50000"}
        result = parse_stream_fields(fields)
        assert result["symbol"] == "BTCUSDT-PERP"
        assert result["price"] == "50000"

    def test_parse_json_value(self):
        fields = {b"data": json.dumps({"key": "val"}).encode()}
        result = parse_stream_fields(fields)
        assert isinstance(result["data"], dict)
        assert result["data"]["key"] == "val"

    def test_parse_array_value(self):
        fields = {b"levels": json.dumps([1, 2, 3]).encode()}
        result = parse_stream_fields(fields)
        assert isinstance(result["levels"], list)


class TestTradeFlags:
    def test_detect_liquidation_long(self):
        is_liq, side = detect_force_liquidation({"force_order": "true", "side": "SELL"})
        assert is_liq is True
        assert side == "long_liq"

    def test_detect_liquidation_short(self):
        is_liq, side = detect_force_liquidation({"force_order": "true", "side": "BUY"})
        assert is_liq is True
        assert side == "short_liq"

    def test_no_liquidation_normal_trade(self):
        is_liq, side = detect_force_liquidation({"side": "BUY"})
        assert is_liq is False

    def test_detect_large_trade_from_flags(self):
        flags = detect_trade_flags({"flags": "large,sweep"})
        assert flags["is_large_trade"] is True
        assert flags["is_sweep"] is True

    def test_detect_large_trade_from_explicit(self):
        flags = detect_trade_flags({"is_large_trade": "true"})
        assert flags["is_large_trade"] is True


class TestRequiresFields:
    def test_all_present(self):
        assert requires_fields({"a": 1, "b": 2}, "a", "b") is True

    def test_missing_field(self):
        assert requires_fields({"a": 1}, "a", "b") is False
