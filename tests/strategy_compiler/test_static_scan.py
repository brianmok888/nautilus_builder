"""Tests for generated artifact static forbidden-reference scan."""
from __future__ import annotations

import pytest

from packages.strategy_compiler.static_scan import (
    scan_generated_artifact,
    StaticScanResult,
)


class TestStaticScan:
    def test_clean_artifact_passes(self):
        code = '''
class MyStrategy:
    """A clean signal preview strategy."""
    execution_authority = False

    def on_bar(self, bar):
        pass
'''
        result = scan_generated_artifact(code)
        assert result.passed is True
        assert len(result.violations) == 0

    def test_submit_order_detected(self):
        code = '''
class BadStrategy:
    def on_bar(self, bar):
        self.submit_order(order)
'''
        result = scan_generated_artifact(code)
        assert result.passed is False
        assert any("submit_order" in v for v in result.violations)

    def test_trade_action_detected(self):
        code = '''
from somewhere import TradeAction
class BadStrategy:
    def go(self):
        return TradeAction(side="BUY")
'''
        result = scan_generated_artifact(code)
        assert result.passed is False
        assert any("TradeAction" in v for v in result.violations)

    def test_live_credentials_detected(self):
        code = '''
class BadStrategy:
    api_key = "my-api-key"
    secret = "my-secret"
'''
        result = scan_generated_artifact(code)
        assert result.passed is False

    def test_execution_authority_true_detected(self):
        code = '''
class BadStrategy:
    execution_authority = True
'''
        result = scan_generated_artifact(code)
        assert result.passed is False
        assert any("execution_authority" in v for v in result.violations)

    def test_exec_eval_import_detected(self):
        code = '''
class BadStrategy:
    def run(self):
        eval("malicious_code")
'''
        result = scan_generated_artifact(code)
        assert result.passed is False

    def test_exec_call_detected(self):
        code = '''
class BadStrategy:
    def run(self):
        exec("malicious_code")
'''
        result = scan_generated_artifact(code)
        assert result.passed is False

    def test_execution_authority_false_allowed(self):
        code = '''
class GoodStrategy:
    execution_authority = False
'''
        result = scan_generated_artifact(code)
        assert result.passed is True
