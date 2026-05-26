from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from typing import Any

from packages.strategy_spec.models import IndicatorSpec, StrategySpec

_RULE_OPERATORS = ("crossed_above", "crossed_below", "gt", "lt", "gte", "lte", "eq")
_PRICE_FIELDS = ("open", "high", "low", "close", "bid", "ask", "mid")


@dataclass
class _IndicatorState:
    spec: IndicatorSpec
    values: deque[float] = field(default_factory=deque)
    ema: float | None = None
    previous_price: float | None = None
    gains: deque[float] = field(default_factory=deque)
    losses: deque[float] = field(default_factory=deque)

    def update(self, price: float) -> float | None:
        indicator_type = self.spec.type.value
        period = int(self.spec.period)
        self.values.append(price)
        while len(self.values) > period:
            self.values.popleft()

        if indicator_type == "EMA":
            alpha = 2.0 / (period + 1.0)
            self.ema = price if self.ema is None else self.ema + alpha * (price - self.ema)
            self.previous_price = price
            return self.ema
        if indicator_type == "SMA":
            self.previous_price = price
            return sum(self.values) / len(self.values)
        if indicator_type == "RSI":
            if self.previous_price is None:
                self.previous_price = price
                return 50.0
            delta = price - self.previous_price
            self.previous_price = price
            self.gains.append(max(delta, 0.0))
            self.losses.append(max(-delta, 0.0))
            while len(self.gains) > period:
                self.gains.popleft()
            while len(self.losses) > period:
                self.losses.popleft()
            avg_gain = sum(self.gains) / max(len(self.gains), 1)
            avg_loss = sum(self.losses) / max(len(self.losses), 1)
            if avg_loss == 0:
                return 100.0 if avg_gain > 0 else 50.0
            rs = avg_gain / avg_loss
            return 100.0 - (100.0 / (1.0 + rs))

        # Unsupported indicator families remain explicit non-signals until a
        # dedicated no-order adapter is implemented for them.
        self.previous_price = price
        return None


class RuleGraphEvaluator:
    """Deterministic no-order evaluator for Builder StrategySpec rule graphs."""

    def __init__(self, spec: StrategySpec) -> None:
        self._spec = spec
        self._states = {name: _IndicatorState(indicator) for name, indicator in spec.indicators.items()}
        self._current_values: dict[str, float | None] = {field: None for field in _PRICE_FIELDS}
        self._previous_values: dict[str, float | None] = {field: None for field in _PRICE_FIELDS}
        self._observations = 0
        self._rule_evaluations = 0
        self._rule_true_counts = {name: 0 for name in spec.rules}
        self._last_rule_values = {name: False for name in spec.rules}

    @classmethod
    def from_payload(cls, payload: dict[str, Any]) -> "RuleGraphEvaluator":
        return cls(StrategySpec.model_validate(payload))

    def update_price(self, price: float) -> dict[str, object]:
        self._observations += 1
        self._previous_values = dict(self._current_values)
        for field in _PRICE_FIELDS:
            self._current_values[field] = price
        for name, state in self._states.items():
            self._current_values[name] = state.update(price)

        rule_values = {name: self._evaluate_rule_block(block) for name, block in self._spec.rules.items()}
        for name, value in rule_values.items():
            if value:
                self._rule_true_counts[name] += 1
        self._last_rule_values = rule_values
        return self.evidence()

    def update_quote_tick(self, tick: object) -> dict[str, object]:
        return self.update_price(_price_from_quote_tick(tick))

    def evidence(self) -> dict[str, object]:
        return {
            "strategy_logic_evaluated": self._observations > 0,
            "signal_observation_count": self._observations,
            "rule_evaluation_count": self._rule_evaluations,
            "rules": {
                name: {
                    "last_value": self._last_rule_values[name],
                    "true_count": self._rule_true_counts[name],
                }
                for name in self._spec.rules
            },
            "order_intent_count": 0,
            "live_trading_enabled": False,
            "execution_authority": False,
            "may_submit_order": False,
        }

    def _evaluate_rule_block(self, block: object) -> bool:
        all_clauses = getattr(block, "all")
        any_clauses = getattr(block, "any")
        if all_clauses is not None:
            return all(self._evaluate_clause(clause) for clause in all_clauses)
        if any_clauses is not None:
            return any(self._evaluate_clause(clause) for clause in any_clauses)
        return False

    def _evaluate_clause(self, clause: object) -> bool:
        for operator in _RULE_OPERATORS:
            operands = getattr(clause, operator)
            if operands is None:
                continue
            self._rule_evaluations += 1
            left = self._resolve(operands[0], current=True)
            right = self._resolve(operands[1], current=True)
            if left is None or right is None:
                return False
            if operator == "crossed_above":
                previous_left = self._resolve(operands[0], current=False)
                previous_right = self._resolve(operands[1], current=False)
                return previous_left is not None and previous_right is not None and previous_left <= previous_right and left > right
            if operator == "crossed_below":
                previous_left = self._resolve(operands[0], current=False)
                previous_right = self._resolve(operands[1], current=False)
                return previous_left is not None and previous_right is not None and previous_left >= previous_right and left < right
            if operator == "gt":
                return left > right
            if operator == "lt":
                return left < right
            if operator == "gte":
                return left >= right
            if operator == "lte":
                return left <= right
            if operator == "eq":
                return left == right
        return False

    def _resolve(self, operand: str | float | int, *, current: bool) -> float | None:
        if isinstance(operand, (int, float)):
            return float(operand)
        values = self._current_values if current else self._previous_values
        value = values.get(operand)
        return float(value) if value is not None else None


def evaluate_strategy_spec_prices(payload: dict[str, Any], prices: list[float]) -> dict[str, object]:
    evaluator = RuleGraphEvaluator.from_payload(payload)
    for price in prices:
        evaluator.update_price(float(price))
    return evaluator.evidence()


def evaluate_strategy_spec_quote_ticks(payload: dict[str, Any], ticks: list[object]) -> dict[str, object]:
    evaluator = RuleGraphEvaluator.from_payload(payload)
    for tick in ticks:
        evaluator.update_quote_tick(tick)
    return evaluator.evidence()


def _price_from_quote_tick(tick: object) -> float:
    bid = float(getattr(tick, "bid_price"))
    ask = float(getattr(tick, "ask_price"))
    return (bid + ask) / 2.0
