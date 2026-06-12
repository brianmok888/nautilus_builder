from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class StrategyStage(str, Enum):
    DRAFT = "draft"
    TESTING = "testing"
    BETA = "beta"
    FINAL = "final"


class StrategyStatus(str, Enum):
    DRAFT = "draft"
    VALIDATED = "validated"
    BACKTESTED = "backtested"
    APPROVED = "approved"
    EXECUTION_READY = "execution_ready"


class CreatedFrom(str, Enum):
    USER = "user"
    AI_BUILDER = "ai_builder"
    IMPORTED = "imported"


class IndicatorType(str, Enum):
    EMA = "EMA"
    SMA = "SMA"
    RSI = "RSI"
    MACD = "MACD"
    ATR = "ATR"
    BOLLINGER_BANDS = "BollingerBands"
    VWAP = "VWAP"


class IndicatorInput(str, Enum):
    CLOSE = "close"


class OutputMode(str, Enum):
    SIGNAL_PREVIEW_ONLY = "signal_preview_only"


class IndicatorSpec(StrictModel):
    type: IndicatorType
    input: IndicatorInput
    period: Annotated[int, Field(gt=0)]


class RuleClause(StrictModel):
    crossed_above: list[str] | None = None
    crossed_below: list[str] | None = None
    gt: list[str | float | int] | None = None
    lt: list[str | float | int] | None = None
    gte: list[str | float | int] | None = None
    lte: list[str | float | int] | None = None
    eq: list[str | float | int] | None = None

    @model_validator(mode="after")
    def validate_single_operator(self) -> "RuleClause":
        populated = [
            name
            for name in ("crossed_above", "crossed_below", "gt", "lt", "gte", "lte", "eq")
            if getattr(self, name) is not None
        ]
        if len(populated) != 1:
            raise ValueError("rule clause must define exactly one supported operator")
        return self


class RuleBlock(StrictModel):
    all: list[RuleClause] | None = None
    any: list[RuleClause] | None = None

    @model_validator(mode="after")
    def validate_rule_block(self) -> "RuleBlock":
        populated = [name for name in ("all", "any") if getattr(self, name) is not None]
        if len(populated) != 1:
            raise ValueError("rule block must define exactly one of all/any")
        return self


class DataRange(StrictModel):
    start: str
    end: str

    @field_validator("start", "end", mode="before")
    @classmethod
    def normalize_datetime_values(cls, value: str | datetime) -> str:
        if isinstance(value, datetime):
            return value.isoformat().replace("+00:00", "Z")
        return value


class RiskBlock(StrictModel):
    position_size_pct: Annotated[float, Field(gt=0, le=1)]
    stop_loss_pct: Annotated[float, Field(gt=0, le=1)]
    take_profit_pct: Annotated[float, Field(gt=0, le=1)]
    max_hold_bars: Annotated[int, Field(gt=0)]


class ValidationFlags(StrictModel):
    bar_close_only: bool
    no_lookahead_required: bool
    requires_backtest_before_shadow: bool
    output_mode: OutputMode


class Provenance(StrictModel):
    created_by: CreatedFrom
    parent_version_id: str | None = None


class StrategySpec(StrictModel):
    schema_version: str
    version: str
    stage: StrategyStage
    status: StrategyStatus
    created_from: CreatedFrom
    is_frozen: bool = False
    adapter_id: str
    venue: str
    instrument_id: str
    bar_type: str
    data_range: DataRange
    indicators: dict[str, IndicatorSpec]
    rules: dict[str, RuleBlock]
    risk: RiskBlock
    validation: ValidationFlags
    provenance: Provenance

    @model_validator(mode="after")
    def enforce_signal_preview_only(self) -> "StrategySpec":
        if self.validation.output_mode != OutputMode.SIGNAL_PREVIEW_ONLY:
            raise ValueError(
                f"output_mode must be signal_preview_only, got {self.validation.output_mode.value}"
            )
        return self
