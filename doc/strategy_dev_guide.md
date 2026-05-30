# Nautilus Builder — Strategy Development Guide

This guide walks you through the complete strategy lifecycle: from writing your first indicator to promoting a strategy for live signal observation.

## Overview

Nautilus Builder uses a **declarative StrategySpec** model. You don't write Python code that calls `submit_order`. Instead, you define:
1. **Indicators** (EMA, RSI, etc.)
2. **Rules** (entry/exit conditions based on indicator values)
3. **Risk parameters** (position sizing, stops, targets)

Builder validates, compiles, and runs your strategy in a **safe, observation-only** pipeline. The execution authority stays with Nautilus-Daedalus, never with Builder.

## Quick Start

### 1. Define Your Strategy

Create a StrategySpec using the Python API:

```python
from packages.strategy_spec.models import *

spec = StrategySpec(
    schema_version="1.0",
    version="0.1.0",
    stage=StrategyStage.DRAFT,
    status=StrategyStatus.DRAFT,
    created_from=CreatedFrom.USER,
    adapter_id="binance",
    venue="BINANCE",
    instrument_id="BTCUSDT-PERP.BINANCE",
    bar_type="BTCUSDT-PERP.BINANCE-5-MINUTE-LAST-EXTERNAL",
    data_range=DataRange(start="2024-01-01T00:00:00Z", end="2024-06-01T00:00:00Z"),
    indicators={
        "ema_fast": IndicatorSpec(type=IndicatorType.EMA, input=IndicatorInput.CLOSE, period=10),
        "ema_slow": IndicatorSpec(type=IndicatorType.EMA, input=IndicatorInput.CLOSE, period=20),
    },
    rules={
        "entry_long": RuleBlock(all=[RuleClause(crossed_above=["ema_fast", "ema_slow"])]),
        "exit_long": RuleBlock(all=[RuleClause(crossed_below=["ema_fast", "ema_slow"])]),
    },
    risk=RiskBlock(position_size_pct=0.02, stop_loss_pct=0.05, take_profit_pct=0.10, max_hold_bars=60),
    validation=ValidationFlags(
        bar_close_only=True,
        no_lookahead_required=True,
        requires_backtest_before_shadow=True,
        output_mode=OutputMode.SIGNAL_PREVIEW_ONLY,
    ),
    provenance=Provenance(created_by=CreatedFrom.USER),
)
```

### 2. Validate Your Strategy

Builder enforces hard rules:

```python
from packages.strategy_validation.validators import validate_strategy_spec

report = validate_strategy_spec(spec.model_dump(mode="json"))
if not report.is_valid:
    for error in report.errors:
        print(f"ERROR: {error}")
```

**What gets validated:**
- No forbidden references (`submit_order`, `TradeAction`, `eval`, `exec`, etc.)
- No raw code patterns (no shell access, no network calls)
- Risk block present with valid parameters
- `bar_close_only` and `no_lookahead_required` are `True`
- Indicator periods are positive integers
- Each rule has exactly one operator

### 3. Compile Your Strategy

```python
from packages.strategy_compiler.compiler import compile_strategy_spec

artifact = compile_strategy_spec(spec.model_dump(mode="json"), profile="backtest")
print(f"Compiled: {artifact.strategy_class}")
print(f"Authority: {artifact.execution_authority}")  # Always False in Builder
```

### 4. Run a Backtest

```python
from packages.backtest_runner.config_builder import build_backtest_config

config = build_backtest_config(
    strategy_spec_version=spec.version,
    adapter_id=spec.adapter_id,
    instrument_id=spec.instrument_id,
    compile_hash=artifact.compile_hash,
    validation_report_id="val-001",
    worker_image="nautilus-builder-worker:latest",
)
```

The backtest config is sent to the worker process. Builder itself never runs trading code — it generates configuration that the backend worker uses.

### 5. Promote to Signal Observation

After successful backtest, you can request a promotion:

```python
from packages.lifecycle.models import LifecycleCommand

# Strategy moves through stages:
# DRAFT → TESTING → BETA → FINAL
```

Promotion requires evidence: validation report, backtest results, no-lookahead confirmation.

## Indicator Reference

| Indicator | Type | Parameters | Description |
|-----------|------|------------|-------------|
| EMA | `IndicatorType.EMA` | `period: int` | Exponential Moving Average |
| SMA | `IndicatorType.SMA` | `period: int` | Simple Moving Average |
| RSI | `IndicatorType.RSI` | `period: int` | Relative Strength Index |
| MACD | `IndicatorType.MACD` | `period: int` | Moving Average Convergence Divergence |
| ATR | `IndicatorType.ATR` | `period: int` | Average True Range |
| BollingerBands | `IndicatorType.BollingerBands` | `period: int` | Bollinger Bands |
| VWAP | `IndicatorType.VWAP` | `period: int` | Volume Weighted Average Price |

## Rule Operators

Rules define entry/exit conditions using these operators:

| Operator | Description | Example |
|----------|-------------|---------|
| `crossed_above` | Indicator A crossed above B | `["ema_fast", "ema_slow"]` |
| `crossed_below` | Indicator A crossed below B | `["ema_fast", "ema_slow"]` |
| `gt` | Greater than | `["rsi", 70]` |
| `lt` | Less than | `["rsi", 30]` |
| `gte` | Greater than or equal | `["ema_fast", "ema_slow"]` |
| `lte` | Less than or equal | `["ema_fast", "ema_slow"]` |
| `eq` | Equal to | `["signal", 0]` |

Rules can be combined with `all` (AND) or `any` (OR) logic:

```python
RuleBlock(
    all=[RuleClause(lt=["rsi", 30])],  # All conditions must be true
)
RuleBlock(
    any=[RuleClause(gt=["rsi", 70]), RuleClause(lt=["rsi", 20])],  # Any condition true
)
```

## Risk Parameters

| Parameter | Type | Range | Description |
|-----------|------|-------|-------------|
| `position_size_pct` | float | 0 < x ≤ 1 | Fraction of portfolio per trade |
| `stop_loss_pct` | float | 0 < x ≤ 1 | Maximum loss per trade |
| `take_profit_pct` | float | 0 < x ≤ 1 | Target profit per trade |
| `max_hold_bars` | int | > 0 | Maximum bars before forced exit |

## Available Adapters

Use the adapter registry to see what's available:

```python
from packages.adapter_registry.service import AdapterRegistryService

registry = AdapterRegistryService()
for adapter in registry.list_enabled_adapters():
    print(f"{adapter.adapter_id}: {adapter.venue} ({adapter.asset_class})")
```

## Lifecycle Stages

Strategies progress through these stages:

1. **DRAFT** — Initial creation, editable
2. **TESTING** — Under validation and backtest
3. **BETA** — Shadow/signals-only observation
4. **FINAL** — Promotion candidate (requires full evidence chain)

## Safety Boundaries

Builder enforces these hard rules:

- **No execution authority** — Builder never submits orders
- **No raw code** — No `eval`, `exec`, `subprocess`, `socket`, `requests`
- **No forbidden references** — No `submit_order`, `TradeAction`, `close_position`
- **Bar-close-only** — Strategies use close prices, not intrabar
- **No lookahead** — Strategies cannot see future data
- **Advisory AI** — AI output is always draft-stage, requires validation

## Running the Demos

```bash
# Basic: spec → validate → compile
python3 docs/examples/demo_strategy_basic.py

# Full pipeline: spec → validate → compile → backtest config
python3 docs/examples/demo_strategy_backtest.py

# Adapter registry exploration
python3 docs/examples/demo_adapter_discovery.py
```

## Next Steps

- Read `doc/nautilus_builder_spec.md` for the full product specification
- Read `doc/nautilus_builder_hardguards.md` for safety boundaries
- Read `DEVELOPMENT.md` for development environment setup
- Explore `docs/examples/` for runnable demo scripts

## Running the End-to-End Pipeline

The `scripts/run_backtest.py` script chains all seams into a single flow:

```bash
# Run with a JSON spec file
python scripts/run_backtest.py --spec docs/examples/specs/dual_ma.json

# Run with JSON output (for scripting/CI)
python scripts/run_backtest.py --spec docs/examples/specs/dual_ma.json --json

# Save result to file
python scripts/run_backtest.py --spec docs/examples/specs/rsi_reversal.json --output results/

# See help
python scripts/run_backtest.py --help
```

### What happens in 30 seconds

```
Load JSON spec → Validate → Compile → Run backtest → Print result
     0.000s        0.001s     0.000s      0.000s        0.002s total
```

The pipeline:
1. **Loads** the JSON spec file and parses it as a `StrategySpec`
2. **Validates** against all hard rules (no forbidden refs, risk block present, etc.)
3. **Compiles** to a `CompileArtifact` with `execution_authority=False`
4. **Runs backtest** in fixture mode (no venue connection needed)
5. **Prints** a human-readable report (or JSON with `--json`)

### Example output

```
================================================================
  Nautilus Builder — Backtest Pipeline Result
================================================================
  Spec:        v1.0.0
  Instrument:  BTCUSDT-PERP.BINANCE
  Adapter:     binance
  Indicators:  ema_fast, ema_slow
  Rules:       entry_long, exit_long
  NT Version:  1.227.0

  Validation:  PASSED

  Compile:     backtest
  Class:       RuleGraphBacktestStrategy
  Authority:   False
  Hash:        5026d42a740bc15c...

  Backtest:
    Trades:    1
    Return:    0.0000
    trade_count: 1
    fill_count: 1

  Timing:      0.002s total
================================================================
  Pipeline complete.
================================================================
```

### Creating your own spec

1. Copy an example spec:
   ```bash
   cp docs/examples/specs/dual_ma.json my_strategy.json
   ```

2. Edit the spec with your indicators, rules, and risk parameters.

3. Run the pipeline:
   ```bash
   python scripts/run_backtest.py --spec my_strategy.json
   ```

4. If validation passes, you can use the JSON output in CI:
   ```bash
   python scripts/run_backtest.py --spec my_strategy.json --json | jq '.is_valid'
   ```
