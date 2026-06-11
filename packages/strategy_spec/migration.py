"""StrategySpec v1 to v2 migration.

Converts classic StrategySpec (v1) models into StrategySpecV2 format
while preserving backward compatibility.
"""
from __future__ import annotations

from packages.strategy_spec.models import StrategySpec as StrategySpecV1
from packages.strategy_spec.models_v2 import (
    ConditionDSL,
    ConditionPrimitive,
    FeatureGroup,
    FeatureInput,
    RiskContractV2,
    SchemaVersion,
    StrategySpecV2,
    StrategySpecV2Metadata,
    StrategySpecV2Universe,
)


def _map_indicator_type_to_feature(key: str, indicator_type: str) -> FeatureInput:
    """Map v1 indicator types to v2 feature groups."""
    mapping = {
        "EMA": FeatureGroup.TRADES,
        "SMA": FeatureGroup.TRADES,
        "RSI": FeatureGroup.TRADES,
        "MACD": FeatureGroup.TRADES,
        "ATR": FeatureGroup.TRADES,
        "BollingerBands": FeatureGroup.TRADES,
        "VWAP": FeatureGroup.VWAP,
    }
    return FeatureInput(
        group=mapping.get(indicator_type, FeatureGroup.TRADES),
        name=key,
        required=True,
    )


def migrate_v1_to_v2(spec_v1: StrategySpecV1) -> StrategySpecV2:
    """Convert a v1 StrategySpec into v2 format."""
    feature_inputs = [
        _map_indicator_type_to_feature(key, ind.type.value)
        for key, ind in spec_v1.indicators.items()
    ]

    # Build conditions from v1 rules
    conditions: list[ConditionDSL] = []
    for rule_name, block in spec_v1.rules.items():
        clauses = block.all or block.any or []
        for clause in clauses:
            operands: list[str | float | int] = []
            if clause.crossed_above:
                operands = clause.crossed_above
            elif clause.crossed_below:
                operands = clause.crossed_below
            elif clause.gt:
                operands = clause.gt
            elif clause.lt:
                operands = clause.lt
            elif clause.gte:
                operands = clause.gte
            elif clause.lte:
                operands = clause.lte
            elif clause.eq:
                operands = clause.eq
            if operands:
                conditions.append(
                    ConditionDSL(
                        primitive=ConditionPrimitive.COMPARE,
                        operands=operands,
                    )
                )

    # Extract timeframe from bar_type (format: INSTRUMENT-STEP-AGGREGATION-PRICE-SOURCE)
    timeframe = "1-MINUTE"
    if spec_v1.bar_type:
        parts = spec_v1.bar_type.split("-")
        if len(parts) >= 3:
            timeframe = f"{parts[-3]}-{parts[-2]}"

    return StrategySpecV2(
        metadata=StrategySpecV2Metadata(
            strategy_id=f"{spec_v1.adapter_id}_{spec_v1.venue}_{spec_v1.instrument_id}",
            lineage_id=f"{spec_v1.adapter_id}_{spec_v1.venue}_{spec_v1.instrument_id}",
            name=f"Migrated from v1 ({spec_v1.version})",
            version=spec_v1.version,
            schema_version=SchemaVersion.V2,
            created_by=spec_v1.created_from.value,
        ),
        universe=StrategySpecV2Universe(
            venue=spec_v1.venue,
            instrument_id=spec_v1.instrument_id,
            timeframe=timeframe,
        ),
        feature_inputs=feature_inputs,
        conditions=conditions,
        risk_contract=RiskContractV2(
            max_spread_bps=100.0,
            max_position_notional=10000.0,
            max_daily_loss=1000.0,
        ),
    )
