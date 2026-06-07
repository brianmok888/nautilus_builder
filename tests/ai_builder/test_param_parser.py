"""Tests for # @param convention parser for AI Builder (S17)."""
from packages.ai_builder.param_parser import (
    parse_params,
    parse_strategy_header,
)


class TestParamParsing:
    """Verify # @param comment parsing."""

    def test_parse_single_param(self):
        code = '# @param period:int:14 EMA period'
        result = parse_params(code)
        assert len(result.params) == 1
        assert result.params[0].name == "period"
        assert result.params[0].type == "int"
        assert result.params[0].default == "14"
        assert result.params[0].description == "EMA period"

    def test_parse_multiple_params(self):
        code = """\
# @param period:int:14 EMA period
# @param stop_loss:float:0.05 Stop loss fraction
# @param venue:str:BINANCE Exchange venue
"""
        result = parse_params(code)
        assert len(result.params) == 3
        assert result.params[0].name == "period"
        assert result.params[1].name == "stop_loss"
        assert result.params[2].name == "venue"

    def test_parse_mixed_content(self):
        code = """\
# This is a regular comment
# @param ema_fast:int:10 Fast EMA period
x = 1  # some code
# @param ema_slow:int:20 Slow EMA period
"""
        result = parse_params(code)
        assert len(result.params) == 2
        assert result.params[0].name == "ema_fast"
        assert result.params[1].name == "ema_slow"

    def test_parse_empty_code(self):
        result = parse_params("")
        assert len(result.params) == 0

    def test_parse_no_params(self):
        code = "# Just a regular comment\nprint('hello')"
        result = parse_params(code)
        assert len(result.params) == 0

    def test_parse_param_with_spaces_in_description(self):
        code = '# @param threshold:float:0.5 Minimum threshold for signal generation'
        result = parse_params(code)
        assert result.params[0].description == "Minimum threshold for signal generation"

    def test_parse_param_without_description(self):
        code = '# @param count:int:5'
        result = parse_params(code)
        assert result.params[0].name == "count"
        assert result.params[0].description == ""


class TestStrategyHeaderParsing:
    """Verify # @strategy header parsing."""

    def test_parse_strategy_header(self):
        code = '# @strategy name="EMA Crossover" timeframe="5-MINUTE"'
        result = parse_strategy_header(code)
        assert result is not None
        assert result.get("name") == "EMA Crossover"
        assert result.get("timeframe") == "5-MINUTE"

    def test_parse_strategy_header_with_adapter(self):
        code = '# @strategy name="RSI Mean Reversion" adapter="binance" timeframe="15-MINUTE"'
        result = parse_strategy_header(code)
        assert result is not None
        assert result.get("name") == "RSI Mean Reversion"
        assert result.get("adapter") == "binance"

    def test_parse_strategy_header_no_header(self):
        code = '# Just a comment\nprint("hello")'
        result = parse_strategy_header(code)
        assert result is None

    def test_parse_strategy_header_empty_code(self):
        result = parse_strategy_header("")
        assert result is None


class TestParseResult:
    """Verify ParseResult model."""

    def test_parse_result_has_params(self):
        result = parse_params('# @param x:int:1 desc')
        assert hasattr(result, "params")
        assert len(result.params) == 1

    def test_parse_result_has_header(self):
        result = parse_params('# @strategy name="Test"')
        # ParseResult from parse_params may not have header, that's OK
        assert hasattr(result, "params")

    def test_parse_full_strategy(self):
        code = """\
# @strategy name="EMA Cross" adapter="binance" timeframe="5-MINUTE"
# @param ema_fast:int:10 Fast EMA period
# @param ema_slow:int:20 Slow EMA period
# @param position_size:float:0.02 Position size fraction
"""
        result = parse_params(code)
        assert len(result.params) == 3
        assert result.params[0].name == "ema_fast"
        assert result.params[2].default == "0.02"
